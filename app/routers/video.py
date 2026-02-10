from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime

from app.db.database import get_db
from app.models.user import User
from app.models.video import Video, VideoTranscribe
from app.schemas.video import Video as VideoSchema, VideoCreate, Transcription as TranscriptionSchema
from app.dependencies import get_current_user
from app.services.video_processing import extract_audio_from_video, google_transcribe, assembly_transcribe
from chatbot import process_transcribed_video_text, UNIFIED_VECTOR_STORE

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.post("/upload", response_model=VideoSchema)
def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    upload_dir = "uploaded_videos"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    new_video = Video(
        user_id=current_user.id,
        video_name=file.filename,
        video_path=file_path
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    return new_video

@router.post("/{video_id}/transcribe", response_model=TranscriptionSchema)
def transcribe_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    if video.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to transcribe this video")

    # Extract Audio
    try:
        audio_path = extract_audio_from_video(video.video_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio extraction failed: {str(e)}")

    # Transcribe (Default to Google for now, or add query param? User code had engine selection logic in upload)
    # But here we are just triggering transcription. Let's use Google by default or AssemblyAI if key exists.
    # The user provided functions `google_transcribe` and `assembly_transcribe`.
    # Let's try Google first as per their previous code preference unless engine is specified.
    # Actually, I'll use google_transcribe for simplicity as requested, or maybe catch error.
    
    # Transcribe with Timestamps
    from app.services.video_processing import transcribe_video_chunks
    
    # Get chunks with timestamps
    import traceback
    try:
        chunks = transcribe_video_chunks(video.video_path)
    except Exception as e:
        print(f"Transcription Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transcription process failed: {str(e)}")
    
    if not chunks:
        raise HTTPException(status_code=400, detail="Could not extract any audio/text from the video. Please check if the video has audio.")

    # Process for RAG (indexes metadata)
    process_transcribed_video_text(UNIFIED_VECTOR_STORE, chunks)
    
    # Flatten text for database storage
    full_text = "\n".join([c['text'] for c in chunks])
    
    new_transcription = VideoTranscribe(
        video_id=video_id,
        user_id=current_user.id,
        transcription_text=full_text
    )
    db.add(new_transcription)
    db.commit()
    db.refresh(new_transcription)
    return new_transcription

import os
import shutil
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from moviepy import VideoFileClip

import speech_recognition as sr
import assemblyai as aai

from chatbot import (
    extract_text_from_pdf,
    split_text_into_chunks,
    create_vector_store,
    process_transcribed_video_text,
    get_insights_from_video,
    UNIFIED_VECTOR_STORE
)

from chatbot_repo import save_chat_to_db
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# FastAPI App Setup
# ---------------------------

app = FastAPI(
    title="AI Knowledge Base Chatbot",
    description="Handles PDFs, Videos, Speech Recognition, RAG Chat",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)


# ---------------------------
# Models
# ---------------------------

class ChatRequest(BaseModel):
    query: str
    transcription: Optional[str] = None


class UploadTranscription(BaseModel):
    text: str


# ---------------------------
# Helper Functions
# ---------------------------

def extract_audio_from_video(video_path: str) -> str:
    """
    Extract WAV audio from MP4, MOV, AVI etc.
    """
    audio_path = video_path.rsplit(".", 1)[0] + ".wav"

    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(
        audio_path,
        fps=16000,
        codec="pcm_s16le"
    )
    clip.close()

    return audio_path


def google_transcribe(audio_path: str) -> str:
    """
    Transcribe audio using Google SpeechRecognition (offline API).
    """
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data, language="en-IN")
        return text
    except Exception as e:
        return f"[Google Speech Error] {e}"


def assembly_transcribe(audio_path: str) -> str:
    """
    Transcribe audio using AssemblyAI cloud API.
    """
    aai.settings.api_key = os.getenv("ASSEMBLYAI_KEY")
    transcriber = aai.Transcriber()

    transcript = transcriber.transcribe(audio_path)
    return transcript.text


# ---------------------------
# API ROUTES
# ---------------------------

@app.get("/")
def home():
    return {"message": "Backend is running! 🎉"}


# ---------------------------
# 1️⃣ Upload PDFs & Store in FAISS
# ---------------------------

@app.post("/upload-pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    os.makedirs("documents", exist_ok=True)
    saved_files = []

    for file in files:
        save_path = f"documents/{file.filename}"

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = extract_text_from_pdf(save_path)
        chunks = split_text_into_chunks(text)
        create_vector_store(UNIFIED_VECTOR_STORE, chunks)

        saved_files.append({
            "file": file.filename,
            "chunks": len(chunks),
            "characters": len(text)
        })

    return {
        "message": "PDFs added successfully!",
        "files": saved_files
    }


# ---------------------------
# 2️⃣ Upload Video → Transcribe → Add to FAISS
# ---------------------------

@app.post("/upload-videos")
async def upload_videos(
    files: List[UploadFile] = File(...),
    engine: str = "google"
):
    os.makedirs("videos", exist_ok=True)
    results = []

    for file in files:
        video_path = f"videos/{file.filename}"

        # Save uploaded video
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract audio
        audio_path = extract_audio_from_video(video_path)

        # Choose transcription engine
        if engine.lower() == "assemblyai":
            text = assembly_transcribe(audio_path)
        else:
            text = google_transcribe(audio_path)
            
        print(f"\n[TRANSCRIPTION for {file.filename}]:\n{text}\n" + "-"*50)

        # Add transcription to knowledge base
        process_transcribed_video_text(UNIFIED_VECTOR_STORE, text)

        results.append({
            "file": file.filename,
            "chars": len(text),
            "engine_used": engine,
            "audio_file": audio_path
        })

    return {"processed": results}


# ---------------------------
# 3️⃣ Upload raw transcription text directly
# ---------------------------

@app.post("/upload-transcription")
async def upload_transcription(payload: UploadTranscription):
    process_transcribed_video_text(UNIFIED_VECTOR_STORE, payload.text)
    return {"message": "Transcription added to knowledge base!"}


# ---------------------------
# 4️⃣ CHAT API
# ---------------------------

@app.post("/chat")
async def chat_api(request: ChatRequest):
    print(f"\n[USER QUERY]: {request.query}")
    answer = get_insights_from_video(
        request.query,
        request.transcription
    )

    # Save to SQL Server
    # save_chat_to_db(request.query, answer)
    print(f"[BOT ANSWER]: {answer}\n" + "-"*50)

    return {"answer": answer}


# ---------------------------
# 5️⃣ Knowledge Base Status
# ---------------------------

@app.get("/kb-status")
async def kb_status():
    if not os.path.exists(UNIFIED_VECTOR_STORE):
        return {"exists": False, "total_chunks": 0}

    try:
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = FAISS.load_local(
            UNIFIED_VECTOR_STORE,
            embeddings,
            allow_dangerous_deserialization=True
        )

        return {
            "exists": True,
            "total_chunks": vector_store.index.ntotal
        }

    except Exception as e:
        return {"exists": False, "error": str(e)}


# ---------------------------
# 🚀 RUN SERVER

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)



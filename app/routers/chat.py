from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from app.db.database import get_db
from sqlalchemy.orm import Session
# Import existing chatbot logic (assuming chatbot.py is in root, we might need to adjust path or move it)
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")
from chatbot import get_insights_from_video, process_transcribed_video_text, UNIFIED_VECTOR_STORE

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    query: str
    transcription: Optional[str] = None

class UploadTranscription(BaseModel):
    text: str

@router.post("/")
async def chat_api(request: ChatRequest):
    print(f"\n[USER QUERY]: {request.query}")
    # Using the existing RAG function
    answer = get_insights_from_video(
        request.query,
        request.transcription
    )
    print(f"[BOT ANSWER]: {answer}\n" + "-"*50)
    return answer

@router.post("/upload-transcription")
async def upload_transcription(payload: UploadTranscription):
    process_transcribed_video_text(UNIFIED_VECTOR_STORE, payload.text)
    return {"message": "Transcription added to knowledge base!"}

@router.get("/kb-status")
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

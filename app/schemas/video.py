from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VideoBase(BaseModel):
    video_name: str
    video_path: str

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    user_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class TranscriptionBase(BaseModel):
    transcription_text: str

class TranscriptionCreate(TranscriptionBase):
    pass

class Transcription(TranscriptionBase):
    id: int
    user_id: int
    video_id: int
    transcribed_at: datetime

    class Config:
        from_attributes = True

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_name = Column(String)
    video_path = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("app.models.user.User", back_populates="videos")
    transcriptions = relationship("VideoTranscribe", back_populates="video")

class VideoTranscribe(Base):
    __tablename__ = "videotranscribe"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    transcription_text = Column(Text)
    transcribed_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="transcriptions")
    user = relationship("app.models.user.User", back_populates="transcriptions")

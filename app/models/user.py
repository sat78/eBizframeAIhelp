from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    videos = relationship("app.models.video.Video", back_populates="user")
    transcriptions = relationship("app.models.video.VideoTranscribe", back_populates="user")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.routers import auth, video, chat
import app.models.user
import app.models.video

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Video Transcription API",
    description="FastAPI with PostgreSQL and JWT Auth",
    version="2.0.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(video.router)
app.include_router(chat.router)

@app.get("/")
def home():
    return {"message": "Video Transcription API with PostgreSQL is running! 🚀"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8010, reload=True)

import os
import speech_recognition as sr
import assemblyai as aai
from moviepy import VideoFileClip
from dotenv import load_dotenv

load_dotenv()

def extract_audio_from_video(video_path: str) -> str:
    """
    Extract WAV audio from MP4, MOV, AVI etc.
    """
    # Create audio path by replacing extension
    base, _ = os.path.splitext(video_path)
    audio_path = f"{base}.wav"

    # Load video and export audio
    clip = VideoFileClip(video_path)
    # Using pcm_s16le codec for compatibility with speech recognition
    clip.audio.write_audiofile(
        audio_path,
        fps=16000,
        nbytes=2,
        codec="pcm_s16le",
        logger=None # Suppress moviepy logging
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
        # Using en-IN as requested
        text = recognizer.recognize_google(audio_data, language="en-IN")
        return text
    except Exception as e:
        return f"[Google Speech Error] {e}"

def assembly_transcribe(audio_path: str) -> str:
    """
    Transcribe audio using AssemblyAI cloud API.
    """
    if not os.getenv("ASSEMBLYAI_KEY"):
        return "[Error] AssemblyAI API Key not found."

    aai.settings.api_key = os.getenv("ASSEMBLYAI_KEY")
    transcriber = aai.Transcriber()

    try:
        transcript = transcriber.transcribe(audio_path)
        if transcript.status == aai.TranscriptStatus.error:
             return f"[AssemblyAI Error] {transcript.error}"
        return transcript.text
    except Exception as e:
        return f"[AssemblyAI Exception] {e}"

def transcribe_video_chunks(video_path: str, chunk_duration: int = 30):
    """
    Split video into chunks and transcribe each to get timestamps.
    Returns: List[Dict] -> [{"text": "...", "start": 0, "end": 30}, ...]
    """
    results = []
    # Removed blanket try-except to debug 500 error
    clip = VideoFileClip(video_path)
    duration = clip.duration
    
    for start in range(0, int(duration), chunk_duration):
        end = min(start + chunk_duration, duration)
        
        # Create a temporary chunk audio file
        # Use absolute path for temp file to avoid CWD issues
        chunk_audio_path = os.path.abspath(f"temp_chunk_{start}_{end}.wav")
        
        # Extract audio for this chunk
        subclip = clip.subclipped(start, end)
        
        # Check if audio exists
        if subclip.audio is None:
            print(f"No audio found in chunk {start}-{end}")
            continue
            
        subclip.audio.write_audiofile(
            chunk_audio_path,
            fps=16000,
            nbytes=2,
            codec="pcm_s16le",
            logger=None
        )
        
        # Transcribe
        try:
            text = google_transcribe(chunk_audio_path)
        except Exception as e:
            text = f"[Transcription Failed: {str(e)}]"
            print(f"Chunk {start} transcription failed: {e}")

        if text and not text.startswith("[Google Speech Error]"):
            results.append({
                "text": text,
                "start": start,
                "end": end
            })
        
        # Cleanup temp file
        if os.path.exists(chunk_audio_path):
            os.remove(chunk_audio_path)
            
    clip.close()
    return results

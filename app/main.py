import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.transcript import TranscriptError,  extract_video_id, get_sentences

app = FastAPI(title = "English Study Web")

# Websites allowed to call this API from a browser.
# Add your real domain later via the ALLOWED_ORIGINS environment variable,
# for example: ALLOWED_ORIGINS="https://myapp.com,https://www.myapp.com"
DEFAULT_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",   # VS Code Live Server
    "http://127.0.0.1:5500",
]

origins = os.getenv("ALLOWED_ORIGINS", ",".join(DEFAULT_ORIGINS)).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def home ():
        return {"message": "Hello, English learner"}

@app.get("/api/health")
def health():
        return {"status" : "ok"}

@app.get("/api/transcript")
def transcript(url: str):
        try:
            video_id = extract_video_id(url)
            sentences = get_sentences(video_id)
        except TranscriptError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

        return {
        "video_id": video_id,
        "count": len(sentences),
        "sentences": sentences,
    }
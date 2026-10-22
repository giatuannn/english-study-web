from fastapi import FastAPI, HTTPException

from app.transcript import extract_video_id, get_sentences

app = FastAPI(title = "English Study Web")

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
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        try:
            sentences = get_sentences(video_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Could not get transcript: {e}")

        return {
        "video_id": video_id,
        "count": len(sentences),
        "sentences": sentences,
    }
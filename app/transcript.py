import re
from youtube_transcript_api import YouTubeTranscriptApi


def  extract_video_id(url:str) -> str:
    """Get the 11-character video ID from a Youtube URL."""
    match = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([\w-]{11})", url)
    if not match:
        raise ValueError("Invalid Youtube URL")
    return match.group(1)

def merge_into_sentences(snippets) ->list[dict]:
    """Captions come as short fragment. Join them until a sentence ends."""
    sentences, buffer, start, end = [], [], None, 0.0

    for s  in snippets:
        if start is None:
            start = s.start
        buffer.append(s.text.replace("\n", " ").strip())
        end = s.start + s.duration
        if re.search(r"[.?!][\"')]?$", s.text.strip()):
            sentences.append({
                "start": round(start, 1),
                "end": round(end, 1),
                "text": " ".join(buffer).strip(),
            })
            buffer, start = [], None

    # keep the last fragment even if it has no ending punctuation
    if buffer:
        sentences.append({
            "start": round(start, 1),
            "end": round(end, 1),
            "text": " ".join(buffer).strip(),
        })
    return sentences

def get_sentences(video_id: str) -> list[dict]:
    fetched = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
    return merge_into_sentences(fetched)
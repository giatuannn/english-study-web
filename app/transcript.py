import html
import re

from youtube_transcript_api import YouTubeTranscriptApi

SENTENCE_END = re.compile(r"[.?!…][\"')\]]?$")
ABBREVIATIONS = {"mr.", "mrs.", "ms.", "dr.", "prof.", "vs.", "e.g.", "i.e."}

MAX_WORDS = 30   # force a split after this many words
MAX_GAP = 1.5    # seconds of silence that also ends a sentence

class TranscriptError(Exception):
    """An error we can show to the user."""
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


ERROR_MAP = {
        "TranscriptsDisabled": (422, "This video has no captions."),
        "NoTranscriptFound": (422, "This video has no English captions."),
        "VideoUnavailable": (404, "This video is private, deleted or unavailable."),
        "VideoUnplayable": (404, "This video is private, deleted or unavailable."),
        "InvaildVideoID": (400, "That doesn't look like a Youtuble link."),
        "AgeRestricted": (403,  "This video is age-restricted"),
        "IpBlocked": (503, "Youtube is blocking requests right now. Try again later."),
        "RequestBlocked": (503, "Youtube is blocking requests right now. Try again later.")
}

def extract_video_id(url: str) -> str:
    """Get the 11-character video ID from a YouTube URL."""
    match = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([\w-]{11})", url or "")
    if not match:
        raise TranscriptError(400, "That doesn't look like a Youtube link.")
    return match.group(1)


def clean_text(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", " ", text)   # [Music], [Applause]
    text = text.replace("♪", " ").replace(">>", " ")
    text = re.sub(r"^\s*-\s+", "", text)      # leading dialogue dash
    return re.sub(r"\s+", " ", text).strip()


def snippets_to_words(snippets) -> list[dict]:
    """Split each caption fragment into words with estimated timestamps."""
    words = []
    for s in snippets:
        raw = html.unescape(s.text).replace("\n", " ")
        new_speaker = raw.lstrip().startswith(">>")
        tokens = clean_text(raw).split()
        if not tokens:
            continue
        step = s.duration / len(tokens)
        for i, token in enumerate(tokens):
            words.append({
                "text": token,
                "start": s.start + i * step,
                "end": s.start + (i + 1) * step,
                "break_before": new_speaker and i == 0,
            })
    return words


def is_sentence_end(token: str) -> bool:
    return bool(SENTENCE_END.search(token)) and token.lower() not in ABBREVIATIONS


def last_comma_cut(words: list[dict]):
    """Index to cut after the last comma in the second half, or None."""
    for i in range(len(words) - 1, len(words) // 2 - 1, -1):
        if words[i]["text"].endswith(","):
            return i + 1
    return None


def group_words(words: list[dict]) -> list[dict]:
    sentences, current = [], []

    def flush(upto=None):
        nonlocal current
        part = current if upto is None else current[:upto]
        rest = [] if upto is None else current[upto:]
        if part:
            sentences.append({
                "start": round(part[0]["start"], 1),
                "end": round(part[-1]["end"], 1),
                "text": " ".join(w["text"] for w in part),
            })
        current = rest

    for w in words:
        if current and (w["break_before"] or w["start"] - current[-1]["end"] > MAX_GAP):
            flush()
        current.append(w)
        if is_sentence_end(w["text"]):
            flush()
        elif len(current) >= MAX_WORDS:
            flush(last_comma_cut(current))
    flush()
    return sentences


def merge_into_sentences(snippets) -> list[dict]:
    return group_words(snippets_to_words(snippets))


def get_sentences(video_id: str) -> list[dict]:
    try:
        fetched = YouTubeTranscriptApi().fetch(
            video_id, languages=["en", "en-US", "en-GB"]
            )
    except Exception as e:
        status, message = ERROR_MAP.get(
            type(e).__name__,(500, "Some thing went wrong while getting the captions.")
        )
        print(f"[transcript] {type(e).__name__}: {e}")  # get full detail in the terminal
        raise TranscriptError(status, message) from e
    sentences = merge_into_sentences(fetched)
    if not sentences:
        raise TranscriptError(422, "The cations for this video are empty.")
    return sentences

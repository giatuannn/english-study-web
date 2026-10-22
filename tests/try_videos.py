import sys
from app.transcript import extract_video_id, get_sentences

for url in sys.argv[1:]:
    print("=" * 70)
    print(url)
    try:
        sentences = get_sentences(extract_video_id(url))
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}")
        continue
    
    words = [len(s["text"].split()) for s in sentences]
    print(f"  sentences: {len(sentences)}")
    print(f"  average words per sentence: {sum(words) / len(words):.1f}")
    print(f"  longest sentence: {max(words)} words")
    for s in sentences[:3]:
        print(f"  [{s['start']}-{s['end']}] {s['text']}")
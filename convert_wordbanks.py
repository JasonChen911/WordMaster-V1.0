"""
One-shot converter: TXT word bank files → JSON word banks.
Reads from data/vocabulary/ (TXT) and SQLite DB (examples),
writes to 内置词库请勿删除/ as JSON.

Run once: python convert_wordbanks.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "server"))

# Book name mapping
BOOK_NAMES = {
    "2 高中-乱序.txt": "高中.json",
    "3 四级-乱序.txt": "CET4.json",
    "4 六级-乱序.txt": "CET6.json",
    "5 考研-乱序.txt": "考研.json",
    "6 托福-乱序.txt": "TOEFL.json",
    "2_高中.txt": "高中.json",
    "3_四级.txt": "CET4.json",
    "4_六级.txt": "CET6.json",
    "5_考研.txt": "考研.json",
    "6_托福.txt": "TOEFL.json",
}

def main():
    from database import SessionLocal
    from models import Word, DictionaryEntry, Book

    db = SessionLocal()

    # Build lookup: word → example, illustration (from DB)
    word_examples = {}
    for w in db.query(Word).all():
        if w.example_en:
            word_examples[w.english.lower()] = {
                "example": w.example_en,
                "translation": w.example_cn,
                "illustration": w.illustration or "",
            }

    # Also check DictionaryEntry for additional data
    for de in db.query(DictionaryEntry).all():
        key = de.word.lower()
        if key not in word_examples or not word_examples[key].get("example"):
            if de.example:
                word_examples[key] = {
                    "example": de.example,
                    "translation": de.example_translation or "",
                    "illustration": de.illustration or "",
                }

    # Read TXT files from both locations
    txt_dirs = [
        HERE / "内置词库请勿删除",
        HERE / "data" / "vocabulary",
    ]

    for txt_dir in txt_dirs:
        if not txt_dir.exists():
            continue
        for txt_path in sorted(txt_dir.glob("*.txt")):
            json_name = BOOK_NAMES.get(txt_path.name)
            if not json_name:
                # Fallback: use txt name
                json_name = txt_path.stem + ".json"

            words = []
            with txt_path.open("r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [p.strip() for p in line.split("\t")]
                    if len(parts) < 2:
                        continue
                    # Skip index column if present
                    if parts[0].isdigit() and len(parts) > 1:
                        parts = parts[1:]

                    word_text = parts[0].lower()
                    # Filter obviously bad entries
                    if len(word_text) <= 1 or len(word_text) > 40:
                        continue
                    if not word_text[0].isalpha():
                        continue

                    meaning = parts[1] if len(parts) > 1 else ""
                    extra = word_examples.get(word_text, {})

                    words.append({
                        "word": word_text,
                        "meaning": meaning,
                        "example": extra.get("example", ""),
                        "translation": extra.get("translation", ""),
                        "illustration": extra.get("illustration", ""),
                    })

            if words:
                out_path = HERE / "内置词库请勿删除" / json_name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(words, f, ensure_ascii=False, indent=2)
                print(f"  {json_name}: {len(words)} words")

    db.close()
    print("\nDone. JSON word banks created in 内置词库请勿删除/")

if __name__ == "__main__":
    main()

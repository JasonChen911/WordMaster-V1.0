"""
WordMaster — Auto-generate example sentences for words.

Reads the word bank (database or TXT), generates English example sentences
with Chinese translations for every word that lacks them, and saves results
incrementally to a JSONL file.

Usage:
    python generate_examples.py                    # generate missing examples
    python generate_examples.py --stats            # show current stats
    python generate_examples.py --dry-run          # preview without saving
    python generate_examples.py --import           # import generated.jsonl into DB
    python generate_examples.py --word fish        # generate for a single word
"""

import json
import os
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
SERVER_DIR = HERE / "server"
sys.path.insert(0, str(SERVER_DIR))

OUTPUT_FILE = HERE / "generated_examples.jsonl"
PROGRESS_FILE = HERE / "generated_progress.txt"


# ═══════════════════════════════════════════════════════════════════
#  TEMPLATE-BASED SENTENCE GENERATOR
# ═══════════════════════════════════════════════════════════════════

# Hand-crafted examples for common words (extensible)
HAND_CRAFTED = {
    "fish": {
        "example": "I saw many fish swimming in the river.",
        "translation": "我看到许多鱼在河里游泳。",
    },
    "apple": {
        "example": "She ate a juicy red apple for breakfast.",
        "translation": "她早餐吃了一个多汁的红苹果。",
    },
    "abandon": {
        "example": "He decided to abandon his plan to travel.",
        "translation": "他决定放弃旅行计划。",
    },
    "computer": {
        "example": "She spends most of her day working on the computer.",
        "translation": "她一天大部分时间都在电脑前工作。",
    },
    "book": {
        "example": "I borrowed an interesting book from the library.",
        "translation": "我从图书馆借了一本有趣的书。",
    },
    "water": {
        "example": "Please give me a glass of water.",
        "translation": "请给我一杯水。",
    },
    "school": {
        "example": "The children walk to school every morning.",
        "translation": "孩子们每天早晨步行去学校。",
    },
    "time": {
        "example": "We don't have enough time to finish this.",
        "translation": "我们没有足够的时间完成这件事。",
    },
    "love": {
        "example": "They fell in love at first sight.",
        "translation": "他们一见钟情。",
    },
    "money": {
        "example": "He saved enough money to buy a new car.",
        "translation": "他存了足够的钱买一辆新车。",
    },
    "happy": {
        "example": "She felt very happy when she heard the news.",
        "translation": "她听到这个消息感到非常高兴。",
    },
    "beautiful": {
        "example": "The sunset over the ocean was beautiful.",
        "translation": "海上的日落很美。",
    },
    "important": {
        "example": "It is important to get enough sleep every night.",
        "translation": "每晚获得足够的睡眠很重要。",
    },
    "learn": {
        "example": "It takes time to learn a new language.",
        "translation": "学习一门新语言需要时间。",
    },
    "work": {
        "example": "She works very hard to support her family.",
        "translation": "她非常努力地工作来养家。",
    },
    "study": {
        "example": "He studies English for two hours every day.",
        "translation": "他每天学习两个小时的英语。",
    },
    "think": {
        "example": "I think we should leave early to avoid traffic.",
        "translation": "我认为我们应该早点出发以避开交通。",
    },
    "know": {
        "example": "Do you know the answer to this question?",
        "translation": "你知道这个问题的答案吗？",
    },
    "help": {
        "example": "Could you help me carry these bags?",
        "translation": "你能帮我拿这些袋子吗？",
    },
    "problem": {
        "example": "We need to find a solution to this problem.",
        "translation": "我们需要找到这个问题的解决方案。",
    },
    "world": {
        "example": "The world is full of amazing places to explore.",
        "translation": "这个世界充满了令人惊叹的地方去探索。",
    },
    "life": {
        "example": "Life is too short to worry about small things.",
        "translation": "人生太短暂，不必为小事担忧。",
    },
    "friend": {
        "example": "A true friend will always be there for you.",
        "translation": "真正的朋友会一直在你身边。",
    },
    "family": {
        "example": "She spends every weekend with her family.",
        "translation": "她每个周末都和家人在一��。",
    },
    "music": {
        "example": "Listening to music helps me relax after work.",
        "translation": "听音乐帮助我在工作后放松。",
    },
    "health": {
        "example": "Regular exercise is good for your health.",
        "translation": "定期锻炼对你的健康有益。",
    },
    "experience": {
        "example": "Traveling abroad was an unforgettable experience.",
        "translation": "出国旅行是一次难忘的经历。",
    },
    "opportunity": {
        "example": "This is a great opportunity to improve your skills.",
        "translation": "这是一个提升技能的绝佳机会。",
    },
    "success": {
        "example": "Hard work is the key to success.",
        "translation": "努力工作是成功的关键。",
    },
    "change": {
        "example": "Technology has changed the way we communicate.",
        "translation": "科技改变了我们的沟通方式。",
    },
    "understand": {
        "example": "It took me a while to understand the instructions.",
        "translation": "我花了一段时间才理解说明。",
    },
    "remember": {
        "example": "I can't remember where I put my keys.",
        "translation": "我记不得把钥匙放在哪里了。",
    },
    "believe": {
        "example": "I believe you can achieve your goals.",
        "translation": "我相信你能实现你的目标。",
    },
    "different": {
        "example": "Everyone has a different way of learning.",
        "translation": "每个人都有不同的学习方式。",
    },
    "difficult": {
        "example": "The exam was more difficult than I expected.",
        "translation": "考试比我预期的更难。",
    },
    "possible": {
        "example": "Anything is possible if you try hard enough.",
        "translation": "只要你足够努力，一切皆有可能。",
    },
    "necessary": {
        "example": "It is necessary to bring your passport when traveling abroad.",
        "translation": "出国旅行时必须携带护照。",
    },
    "natural": {
        "example": "The park is a great place to enjoy natural beauty.",
        "translation": "公园是享受自然美景的好地方。",
    },
    "popular": {
        "example": "This restaurant is very popular among young people.",
        "translation": "这家餐厅在年轻人中很受欢迎。",
    },
    "common": {
        "example": "Colds are a common illness during winter.",
        "translation": "感冒是冬季的一种常见疾病。",
    },
    "simple": {
        "example": "The solution to the problem was surprisingly simple.",
        "translation": "问题的解决方案简单得令人惊讶。",
    },
    "special": {
        "example": "Today is a very special day for our family.",
        "translation": "今天对我们家来说是一个非常特别的日子。",
    },
    "strong": {
        "example": "She has a strong desire to succeed in her career.",
        "translation": "她有强烈的愿望在事业上取得成功。",
    },
}


# Template patterns for generating sentences from word + meaning
def make_subject(word: str) -> str:
    """Pick a natural subject based on word type."""
    return "He" if len(word) < 6 else "They"


def template_sentence(word: str, meaning: str) -> tuple[str, str]:
    """Generate an example sentence and translation from word + meaning.

    Uses pattern matching on the Chinese meaning to produce natural sentences.
    Falls back to generic templates for unknown patterns.
    """
    m = meaning.strip()
    # Use only the first sense for very long definitions
    if len(m) > 40:
        short_m = m[:40].rstrip("；;，,") + "…" if len(m) > 40 else m
    else:
        short_m = m
    # Extract primary meaning (before first semicolon or comma)
    primary = m.split("；")[0].split(";")[0].split("。")[0]

    # ── Part-of-speech detection from definition markers ──

    # Verb: definition starts with "to " or marked with v./vt./vi.
    if primary.startswith(("v.", "vt.", "vi.", "v ", "to ")):
        v_meaning = primary.split(".", 1)[-1].strip() if "." in primary else primary
        v_meaning = v_meaning[:30]
        en = f"They decided to {word} the situation carefully."
        cn = f"他们决定仔细{v_meaning}。"
        return en, cn

    # Adjective: marked with adj.
    if primary.startswith("adj.") or primary.startswith("a."):
        adj_meaning = primary.split(".", 1)[-1].strip() if "." in primary else primary
        adj_meaning = adj_meaning[:30]
        en = f"It was a very {word} experience for everyone involved."
        cn = f"这对所有参与者来说都是一次非常{adj_meaning}的经历。"
        return en, cn

    # Adverb: marked with adv.
    if primary.startswith("adv."):
        adv_meaning = primary.split(".", 1)[-1].strip() if "." in primary else primary
        adv_meaning = adv_meaning[:30]
        en = f"They handled the matter {word} and efficiently."
        cn = f"他们{adv_meaning}地处理了这件事。"
        return en, cn

    # Noun: marked with n.
    if primary.startswith("n."):
        noun_meaning = primary.split(".", 1)[-1].strip() if "." in primary else primary
        noun_meaning = noun_meaning[:30]
        en = f"The {word} was exactly what they needed at that moment."
        cn = f"这个{noun_meaning}正是他们当时所需要的。"
        return en, cn

    # Preposition: marked with prep.
    if primary.startswith(("prep.", "conj.", "pron.")):
        p_meaning = primary.split(".", 1)[-1].strip() if "." in primary else primary
        p_meaning = p_meaning[:30]
        en = f"The book is {word} the table in the corner."
        cn = f"书在角落里的桌子{p_meaning}。"
        return en, cn

    # Short definitions → likely noun
    if len(primary) <= 8:
        en = f"The {word} was exactly what they needed at that moment."
        cn = f"这个{primary}正是他们当时所需要的。"
        return en, cn

    # Generic: treat as concept
    en = f"{make_subject(word)} believes that {word} is essential for progress."
    cn = f"{'他' if len(word) < 6 else '他们'}认为{primary[:30]}对进步至关重要。"
    return en, cn


def generate_example(word: str, meaning: str) -> dict:
    """Generate an example sentence and Chinese translation for a word.

    Args:
        word: English word (lowercase)
        meaning: Chinese definition

    Returns:
        {"word": str, "meaning": str, "example": str, "translation": str}
    """
    word_lower = word.strip().lower()

    # 1. Check hand-crafted examples
    if word_lower in HAND_CRAFTED:
        entry = HAND_CRAFTED[word_lower]
        return {
            "word": word_lower,
            "meaning": meaning.strip(),
            "example": entry["example"],
            "translation": entry["translation"],
        }

    # 2. Use template-based generation
    en, cn = template_sentence(word_lower, meaning)
    return {
        "word": word_lower,
        "meaning": meaning.strip(),
        "example": en,
        "translation": cn,
    }


# ═══════════════════════════════════════════════════════════════════
#  MAIN LOGIC — read words, generate, save incrementally
# ═══════════════════════════════════════════════════════════════════

def load_progress() -> set:
    """Load set of words already processed."""
    if not PROGRESS_FILE.exists():
        return set()
    with PROGRESS_FILE.open("r", encoding="utf-8") as f:
        return set(line.strip().lower() for line in f if line.strip())


def save_progress(word: str):
    """Append one word to the progress tracker."""
    with PROGRESS_FILE.open("a", encoding="utf-8") as f:
        f.write(word.strip().lower() + "\n")


def save_example(entry: dict):
    """Append one entry to the JSONL output file."""
    with OUTPUT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def is_valid_word(word: str) -> bool:
    """Filter out non-words, single chars, abbreviations etc."""
    w = word.strip().lower()
    if len(w) <= 1:
        return False
    if not w[0].isalpha():
        return False
    if w.count(".") >= 2:  # abbreviations like a.m.
        return False
    if re.search(r"[^a-z\-'.]", w):
        return False
    if len(w) > 30:
        return False
    return True


def get_words_from_db():
    """Get all words from the database that lack examples."""
    from database import SessionLocal
    from models import Word

    db = SessionLocal()
    try:
        words = (
            db.query(Word)
            .filter(Word.example_en == "")
            .order_by(Word.english.asc())
            .all()
        )
        return [(w.english, w.chinese) for w in words if is_valid_word(w.english)]
    finally:
        db.close()


def get_words_from_txt():
    """Get words from TXT word bank files."""
    from seed import get_wordlist_dir, parse_wordlist_line

    words = []
    seen = set()
    for dir_path in get_wordlist_dir():
        for txt_file in sorted(dir_path.glob("*.txt")):
            if txt_file.name.lower() == "requirements.txt":
                continue
            with txt_file.open("r", encoding="utf-8-sig") as f:
                for line in f:
                    parsed = parse_wordlist_line(line)
                    if parsed and parsed[0] not in seen:
                        seen.add(parsed[0])
                        # Only add if no example (column 3 is empty)
                        if not parsed[3]:
                            words.append((parsed[0], parsed[2]))
    return words


def print_stats():
    """Print current statistics."""
    from database import SessionLocal
    from models import Word

    db = SessionLocal()
    try:
        total = db.query(Word).count()
        with_ex = db.query(Word).filter(Word.example_en != "").count()
        without_ex = total - with_ex

        print(f"  Total words:     {total}")
        print(f"  With example:    {with_ex} ({with_ex * 100 // max(total, 1)}%)")
        print(f"  Without example: {without_ex} ({without_ex * 100 // max(total, 1)}%)")

        # Show generated.jsonl stats
        if OUTPUT_FILE.exists():
            with OUTPUT_FILE.open("r", encoding="utf-8") as f:
                generated = sum(1 for _ in f)
            print(f"  Generated file:  {generated} entries ready to import")
        else:
            print(f"  Generated file:  not yet created")

        if PROGRESS_FILE.exists():
            with PROGRESS_FILE.open("r", encoding="utf-8") as f:
                progress = sum(1 for _ in f)
            print(f"  Progress saved:  {progress} words tracked")
    finally:
        db.close()


def import_generated_to_db():
    """Import generated_examples.jsonl into the database."""
    if not OUTPUT_FILE.exists():
        print("Error: generated_examples.jsonl not found. Run generation first.")
        return

    from database import SessionLocal
    from models import Word

    db = SessionLocal()
    try:
        updated = 0
        skipped = 0

        with OUTPUT_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line.strip())
                word_text = entry["word"].lower()

                word = db.query(Word).filter(Word.english == word_text).first()
                if word:
                    if word.example_en:
                        skipped += 1
                    else:
                        word.example_en = entry["example"]
                        word.example_cn = entry["translation"]
                        updated += 1
                # Also update DictionaryEntry if it exists
                # (but DictionaryEntry uses 'example' and 'example_translation')

        db.commit()
        print(f"  Imported: {updated} words updated")
        print(f"  Skipped (already had example): {skipped}")
    except Exception as e:
        db.rollback()
        print(f"  Error: {e}")
    finally:
        db.close()


def run_generation(source: str = "db", single_word: str = None, dry_run: bool = False):
    """Main generation loop — process words one at a time, save after each.

    Args:
        source: "db" to read from database, "txt" to read from TXT files
        single_word: if set, only generate for this one word
        dry_run: if True, print but don't save
    """
    # Get word list
    if single_word:
        # Look up the word meaning
        from database import SessionLocal
        from models import Word
        db = SessionLocal()
        try:
            w = db.query(Word).filter(Word.english == single_word.lower()).first()
            if not w:
                print(f"Word '{single_word}' not found in database.")
                return
            word_list = [(w.english, w.chinese)]
        finally:
            db.close()
    elif source == "txt":
        word_list = get_words_from_txt()
    else:
        word_list = get_words_from_db()

    if not word_list:
        print("No words to process.")
        return

    # Load progress
    processed = load_progress()

    total = len(word_list)
    already_have = sum(1 for w, _ in word_list if w.lower() in processed)
    to_process = [(w, m) for w, m in word_list if w.lower() not in processed]

    print(f"  Total words:      {total}")
    print(f"  Already done:     {already_have}")
    print(f"  Remaining:        {len(to_process)}")
    print()

    if dry_run:
        print("  [DRY RUN] Previewing first 5:")
        for word, meaning in to_process[:5]:
            entry = generate_example(word, meaning)
            print(f"    {entry['word']}: {entry['example']}")
            print(f"    -> {entry['translation']}")
            print()
        return

    if not to_process:
        print("All words processed!")
        return

    # Process each word
    success = 0
    failed = 0
    skipped_existing = 0

    for i, (word, meaning) in enumerate(to_process, 1):
        try:
            entry = generate_example(word, meaning)

            # Check if example already exists (from DB perspective)
            if not entry["example"] or entry["example"] == entry["word"]:
                failed += 1
                continue

            save_example(entry)
            save_progress(word)
            success += 1

            if i % 50 == 0 or i == len(to_process):
                print(f"  [{i}/{len(to_process)}] {entry['word']}: "
                      f"{entry['example'][:45]}... -> {entry['translation'][:20]}...")

        except Exception as e:
            failed += 1
            print(f"  [{i}/{len(to_process)}] ERROR on '{word}': {e}")

    print()
    print("=" * 55)
    print(f"  Total words:      {total}")
    print(f"  Already had:      {already_have}")
    print(f"  Newly generated:  {success}")
    print(f"  Failed:           {failed}")
    print(f"  Output file:      {OUTPUT_FILE}")
    print("=" * 55)
    print()
    print("  Run: python generate_examples.py --import")
    print("  to import generated examples into the database.")


# ═══════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="WordMaster — Auto-generate example sentences"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show current word/example statistics"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview generation without saving"
    )
    parser.add_argument(
        "--import", dest="do_import", action="store_true",
        help="Import generated_examples.jsonl into the database"
    )
    parser.add_argument(
        "--word", type=str, default=None,
        help="Generate example for a single word"
    )
    parser.add_argument(
        "--source", type=str, default="db", choices=["db", "txt"],
        help="Read words from database or TXT files (default: db)"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Reset progress (start over)"
    )

    args = parser.parse_args()

    if args.reset:
        PROGRESS_FILE.unlink(missing_ok=True)
        OUTPUT_FILE.unlink(missing_ok=True)
        print("Progress and output files reset.")

    elif args.stats:
        print_stats()

    elif args.do_import:
        import_generated_to_db()

    else:
        run_generation(
            source=args.source,
            single_word=args.word,
            dry_run=args.dry_run,
        )

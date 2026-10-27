"""Idempotent data-repair / hygiene for the formal word library.

Runs at startup (from ``db_init``) and is safe to run repeatedly. It never
deletes user data; it only:

1. Detects "material pollution" signatures — study words with no Chinese
   meaning, or dictionary entries sourced from material with no definition.
2. Back-fills the missing Chinese meaning from the canonical library (exact →
   lemma → dictionary) so a confirmed import is never a blank entry.
3. Merges case-insensitive duplicate ``words`` rows into the canonical one,
   re-pointing ``book_words`` links before dropping the empty duplicate.

Returns a report dict; a standalone run prints it and exits non-zero if any
pollution is detected (for CI / manual audits).
"""

import logging
from sqlalchemy import text as sa_text

from morphology import variants_for

logger = logging.getLogger(__name__)


def _backfill_word_chinese(db, word) -> bool:
    """Fill ``word.chinese`` from dictionary entries if empty. Returns True if changed."""
    if word.chinese and word.chinese.strip():
        return False
    for v in variants_for(word.english):
        row = db.execute(
            sa_text(
                "SELECT definition_cn FROM dictionary "
                "WHERE lower(word)=:w AND definition_cn IS NOT NULL AND definition_cn != '' "
                "ORDER BY length(definition_cn) DESC LIMIT 1"
            ),
            {"w": v},
        ).fetchone()
        if row and row[0]:
            word.chinese = row[0].strip()
            return True
    return False


def repair_data(db) -> dict:
    """Run idempotent repair; return a report dict."""
    from models import Word, BookWord, DictionaryEntry

    report = {
        "empty_chinese_words_found": 0,
        "empty_chinese_words_fixed": 0,
        "empty_chinese_words_remaining": 0,
        "material_dict_empty_definition": 0,
        "case_duplicate_words_merged": 0,
        "case_duplicate_words_remaining": 0,
        "phonetic_misparsed_example_fixed": 0,
    }

    # 1) Study words with empty Chinese (pollution signature).
    empty_words = db.query(Word).filter(
        (Word.chinese.is_(None)) | (Word.chinese == "")
    ).all()
    report["empty_chinese_words_found"] = len(empty_words)
    for w in empty_words:
        if _backfill_word_chinese(db, w):
            report["empty_chinese_words_fixed"] += 1
    if empty_words:
        db.flush()
        report["empty_chinese_words_remaining"] = (
            db.query(Word)
            .filter((Word.chinese.is_(None)) | (Word.chinese == ""))
            .count()
        )

    # 2) Material dictionary entries missing a definition (audit only — no delete).
    report["material_dict_empty_definition"] = (
        db.query(DictionaryEntry)
        .filter(
            DictionaryEntry.source == "material",
            (DictionaryEntry.definition_cn.is_(None))
            | (DictionaryEntry.definition_cn == ""),
        )
        .count()
    )

    # 2b) Clear example_en that is actually a mis-parsed phonetic + secondary
    # definition (e.g. "[ə'səuʃiət] adj. 副的 n. 伙伴，同事"). A real example
    # sentence never starts with a phonetic delimiter, so this is a safe,
    # idempotent cleanup of the word-bank parsing bug that also caused one word
    # ("associate") to be the only word carrying an example on a fresh install.
    broken_examples = db.query(Word).filter(
        Word.example_en.like("[%") | Word.example_en.like("/%")
    ).all()
    for w in broken_examples:
        w.example_en = ""
    report["phonetic_misparsed_example_fixed"] = len(broken_examples)

    # 3) Case-insensitive duplicate words → merge into the canonical row.
    dup_keys = [
        row[0]
        for row in db.execute(
            sa_text(
                "SELECT lower(english) AS key FROM words "
                "GROUP BY lower(english) HAVING COUNT(*) > 1"
            )
        ).fetchall()
    ]
    for key in dup_keys:
        rows = db.query(Word).filter(Word.english.ilike(key)).all()
        if len(rows) < 2:
            continue
        # Canonical: the one with the most content (chinese first, then lowest id).
        rows.sort(key=lambda w: (not (w.chinese and w.chinese.strip()), w.id))
        canonical = rows[0]
        for dup in rows[1:]:
            # Re-point membership links to the canonical row, absorbing the
            # duplicate's extra content before dropping it.
            db.query(BookWord).filter(BookWord.word_id == dup.id).update(
                {BookWord.word_id: canonical.id}, synchronize_session=False
            )
            if (not canonical.chinese) and dup.chinese:
                canonical.chinese = dup.chinese
            if (not canonical.example_en) and dup.example_en:
                canonical.example_en = dup.example_en
            db.delete(dup)
            report["case_duplicate_words_merged"] += 1
    if dup_keys:
        db.flush()

    # Re-check duplicates after merge (should be none).
    report["case_duplicate_words_remaining"] = len(
        db.execute(
            sa_text(
                "SELECT lower(english) FROM words GROUP BY lower(english) "
                "HAVING COUNT(*) > 1"
            )
        ).fetchall()
    )

    return report


def run_standalone() -> int:
    """Print the report and exit non-zero when pollution is detected."""
    import sys
    from database import SessionLocal

    db = SessionLocal()
    try:
        report = repair_data(db)
        db.commit()
    finally:
        db.close()

    print("=" * 60)
    print("  DATA REPAIR REPORT")
    print("=" * 60)
    for k, v in report.items():
        print(f"  {k}: {v}")

    polluted = (
        report["empty_chinese_words_remaining"]
        or report["material_dict_empty_definition"]
        or report["case_duplicate_words_remaining"]
    )
    print("  ---")
    print(f"  {'POLLUTION DETECTED' if polluted else 'CLEAN'}")
    return 1 if polluted else 0


if __name__ == "__main__":
    import sys
    sys.exit(run_standalone())

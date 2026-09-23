"""AI Gateway + Material Engine tests (offline, no network).

Covers the JSON parsing/repair pipeline and the local material fallback so the
structured-output contract and offline behavior can't silently regress.

Run:  python tests/test_ai_gateway.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

from ai.gateway import _extract_json, _validate, _repair, _strip_code_fence  # noqa: E402
from ai.schemas import MaterialAnalysis, ExtractedWord  # noqa: E402
from ai.services.material_service import clean_text, tokenize, extract_candidates_local  # noqa: E402

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} | {detail}")


print("=" * 60)
print("  AI GATEWAY + MATERIAL ENGINE TESTS (offline)")
print("=" * 60)

# ── 1. Code fence stripping ──
print("\n=== 1. Code fence stripping ===")
raw = '```json\n{"words": []}\n```'
check("strips markdown code fence", _strip_code_fence(raw) == '{"words": []}')

# ── 2. JSON extraction from stray text ──
print("\n=== 2. JSON extraction ===")
stray = 'Sure! Here is the result: {"words": [{"word": "approach"}]} Hope this helps.'
data = _extract_json(stray)
check("extracts embedded JSON object", isinstance(data, dict) and "words" in data)

arr = 'Here: [{"word":"a"},{"word":"b"}] done.'
data2 = _extract_json(arr)
check("extracts embedded JSON array", isinstance(data2, list) and len(data2) == 2)
check("non-JSON returns None", _extract_json("just some text") is None)

# ── 3. Schema validation + repair ──
print("\n=== 3. Schema validation + repair ===")
valid = MaterialAnalysis(words=[{"word": "approach", "importance": 5, "difficulty": 4}])
check("valid object validates", _validate(MaterialAnalysis, valid.model_dump()) is not None)

# Model returns a bare list instead of {"words": [...]} — repair wraps it.
bare = [{"word": "approach", "importance": 5}]
repaired = _repair(MaterialAnalysis, bare)
check("repair wraps a bare list", repaired is not None and repaired.words[0].word == "approach")

# Correct object shape validates directly (no unwrapping needed).
correct = {"words": [{"word": "approach", "importance": 5}]}
check("correct object shape validates", _validate(MaterialAnalysis, correct) is not None)

# Bad type (importance not a number) — validation fails.
check("invalid importance rejected", _validate(MaterialAnalysis, {"words": [{"word": "x", "importance": "not-a-number"}]}) is None)

# ── 4. Text cleaning ──
print("\n=== 4. Text cleaning ===")
md = "**Hello** [world](http://x.com) `code`\n\nNew   line."
cleaned = clean_text(md)
check("markdown stripped", "[world]" not in cleaned and "**" not in cleaned and "`" not in cleaned)
check("whitespace normalized", "   " not in cleaned)

# ── 5. Tokenization filters stopwords ──
print("\n=== 5. Tokenization filters stopwords ===")
toks = tokenize("The approach is to learn the important words")
check("stopwords filtered", "the" not in toks and "is" not in toks and "to" not in toks)
check("content words kept", "approach" in toks and "important" in toks and "learn" in toks)

# ── 6. Local fallback candidates ──
print("\n=== 6. Local fallback candidates ===")
text = ("Artificial intelligence is transforming the way students learn. "
        "Students use intelligent systems to learn. Intelligence drives transformation.")
cands = extract_candidates_local(text, max_words=10)
check("returns candidates", len(cands) > 0)
check("most frequent word first", cands[0].word in ("students", "intelligence", "learn"))
check("candidates are ExtractedWord", all(isinstance(c, ExtractedWord) for c in cands))
check("no stopword candidates", all(c.word not in ("the", "is", "to") for c in cands))

# ── Summary ──
print()
print("=" * 60)
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
print("=" * 60)
sys.exit(1 if FAIL else 0)

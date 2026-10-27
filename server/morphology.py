"""English morphology — normalization and rule-based lemmatization.

WordMaster has no third-party NLP dependency, so this is a small, careful
rule-based layer. Its only job is to turn an *inflected* query word
(e.g. ``students``, ``studies``, ``studied``, ``studying``) into candidate
base forms so a dictionary/search lookup can fall back to the canonical lemma.

Design rules:
- Never strip suffixes blindly. ``bus``/``class``/``news`` are safe because the
  lookup always tries an *exact* match first; lemmatization is only a fallback.
- Each rule emits *several* candidates in best-first order; the caller decides
  which candidate actually exists in the dictionary. This avoids guessing
  between e.g. ``study`` (studies) and ``movie`` (movies).
- The output list is de-duplicated and never contains the input itself.
"""

import re

# ─── Common irregular forms → canonical lemma ────────────────────────────
# Covers high-frequency irregular plurals, past tenses and participles.
_IRREGULAR = {
    # irregular plurals
    "children": "child", "men": "man", "women": "woman", "feet": "foot",
    "teeth": "tooth", "geese": "goose", "mice": "mouse", "people": "person",
    "leaves": "leaf", "knives": "knife", "lives": "life", "wives": "wife",
    "wolves": "wolf", "loaves": "loaf", "sheep": "sheep", "fish": "fish",
    "deer": "deer", "oxen": "ox", "crises": "crisis", "analyses": "analysis",
    "phenomena": "phenomenon", "criteria": "criterion", "data": "datum",
    "media": "medium", "bacteria": "bacterium", "curricula": "curriculum",
    # irregular verbs — past / participle
    "went": "go", "gone": "go", "did": "do", "done": "do", "ate": "eat",
    "eaten": "eat", "saw": "see", "seen": "see", "took": "take", "taken": "take",
    "gave": "give", "given": "give", "came": "come", "became": "become",
    "got": "get", "gotten": "get", "had": "have", "made": "make", "said": "say",
    "thought": "think", "found": "find", "knew": "know", "known": "know",
    "told": "tell", "felt": "feel", "kept": "keep", "left": "leave",
    "brought": "bring", "bought": "buy", "caught": "catch", "taught": "teach",
    "wrote": "write", "written": "write", "ran": "run", "began": "begin",
    "begun": "begin", "broke": "break", "broken": "break", "spoke": "speak",
    "spoken": "speak", "chose": "choose", "chosen": "choose", "drove": "drive",
    "driven": "drive", "flew": "fly", "flown": "fly", "grew": "grow",
    "grown": "grow", "wore": "wear", "worn": "wear", "won": "win",
    "lost": "lose", "meant": "mean", "met": "meet", "paid": "pay",
    "built": "build", "sent": "send", "spent": "spend", "stood": "stand",
    "understood": "understand", "heard": "hear", "held": "hold", "led": "lead",
    "sat": "sit", "sang": "sing", "sung": "sing", "drank": "drink",
    "drunk": "drink", "swam": "swim", "swum": "swim", "rang": "ring",
    "rung": "ring", "sank": "sink", "sunk": "sink", "blew": "blow",
    "blown": "blow", "drew": "draw", "drawn": "draw", "threw": "throw",
    "thrown": "throw", "fell": "fall", "fallen": "fall", "slept": "sleep",
    "sold": "sell", "told": "tell", "read": "read", "rode": "ride",
    "ridden": "ride", "rose": "rise", "risen": "rise", "woke": "wake",
    "woken": "wake", "ate": "eat", "bit": "bite", "bitten": "bite",
    "hid": "hide", "hidden": "hide", "lay": "lie", "lain": "lie",
    "shook": "shake", "shaken": "shake", "stole": "steal", "stolen": "steal",
    "stuck": "stick", "swore": "swear", "sworn": "swear", "tore": "tear",
    "torn": "tear", "wore": "wear", "bore": "bear", "born": "bear",
    "bore": "bear", "beat": "beat", "became": "become", "began": "begin",
    "blew": "blow", "broke": "break", "cut": "cut", "hit": "hit", "put": "put",
    "let": "let", "set": "set", "shut": "shut", "cost": "cost", "hurt": "hurt",
    "spread": "spread", "burst": "burst", "bet": "bet", "cast": "cast",
}

# Words that must never be "de-inflected" even though they end in a suffix.
# The exact-match-first lookup already protects most, but these are extra-safe.
_NEVER_REDUCE = {
    "bus", "news", "class", "pass", "mass", "gas", "yes", "this", "us",
    "as", "is", "was", "has", "his", "plus", "status", "focus", "axis",
    "basis", "crisis", "analysis", "species", "series", "office", "service",
    "practice", "notice", "science", "since", "once", "police", "piece",
    "peace", "space", "face", "race", "place", "price", "voice", "choice",
    "chance", "dance", "change", "charge", "large", "language", "message",
    "page", "image", "stage", "age", "edge", "knowledge", "bridge", "judge",
    "range", "strange", "college", "village", "package", "storage",
}

_TOKEN_RE = re.compile(r"[a-z]+(?:['’-][a-z]+)*")


def normalize(word: str) -> str:
    """Lowercase, trim, and strip surrounding punctuation/whitespace.

    Keeps internal hyphens and apostrophes (e.g. ``well-known``, ``it's``).
    """
    if not isinstance(word, str):
        return ""
    text = word.strip().lower()
    text = re.sub(r"^[^a-z]+", "", text)
    text = re.sub(r"[^a-z]+$", "", text)
    return text


def lemmatize(word: str) -> list[str]:
    """Return candidate base forms for an inflected word, best first.

    The caller looks each candidate up in the dictionary and stops at the first
    hit, so returning a small superset is safe and avoids destructive guesses.
    """
    w = normalize(word)
    if not w or len(w) < 3:
        return []

    cands: list[str] = []

    # 1. Irregular exact form.
    if w in _IRREGULAR:
        cands.append(_IRREGULAR[w])

    # 2. -ied → -y (studied → study, tried → try, cried → cry).
    if w.endswith("ied") and len(w) >= 4:
        cands.append(w[:-3] + "y")

    # 3. -ies → -y (studies → study, flies → fly) and -ies → drop s (movies → movie).
    if w.endswith("ies") and len(w) >= 4:
        cands.append(w[:-3] + "y")
        cands.append(w[:-1])

    # 4. -es → drop es (boxes → box, classes → class, buses → bus, goes → go).
    elif w.endswith("es") and len(w) >= 4 and w not in _NEVER_REDUCE:
        cands.append(w[:-2])
        cands.append(w[:-1])

    # 5. plain -s plural / 3rd-person (cats → cat, students → student, reads → read).
    elif w.endswith("s") and not w.endswith("ss") and len(w) >= 4 and w not in _NEVER_REDUCE:
        cands.append(w[:-1])

    # 6. -ing (studying → study, making → make, running → run).
    if w.endswith("ing") and len(w) >= 5:
        stem = w[:-3]
        cands.append(stem)                 # studying → study, reading → read
        cands.append(stem + "e")           # making → make, writing → write
        if len(stem) >= 3 and stem[-1] == stem[-2]:
            cands.append(stem[:-1])        # running → run, swimming → swim

    # 7. -ed (played → play, loved → love, stopped → stop).
    if w.endswith("ed") and len(w) >= 4:
        stem = w[:-2]
        cands.append(stem)                 # played → play
        cands.append(w[:-1])               # loved → love, used → use
        if len(stem) >= 3 and stem[-1] == stem[-2]:
            cands.append(stem[:-1])        # stopped → stop, planned → plan

    # De-duplicate, drop the input itself and anything trivially short.
    seen: set[str] = set()
    out: list[str] = []
    for c in cands:
        if c and c != w and len(c) >= 2 and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def variants_for(word: str) -> list[str]:
    """Full lookup chain for a query word: normalized form, then lemmas."""
    base = normalize(word)
    if not base:
        return []
    result = [base]
    result.extend(lemmatize(base))
    return result


def lookup_chain(word, finder):
    """Resolve a word via exact → normalized → lemma, using ``finder``.

    ``finder(text)`` should return a truthy result for a match, or None.
    Returns ``(result, matched_word, strategy)``; ``strategy`` is one of
    ``"exact"`` or ``"lemma"``. Returns ``(None, None, None)`` on no match.
    """
    variants = variants_for(word)
    for idx, v in enumerate(variants):
        if not v:
            continue
        result = finder(v)
        if result:
            return result, v, ("exact" if idx == 0 else "lemma")
    return None, None, None

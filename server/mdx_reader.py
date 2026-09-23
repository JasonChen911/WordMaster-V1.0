"""
MDX Dictionary Reader for WordMaster — Professional Edition.

Enhanced parser supporting:
- Word, phonetic (US/UK), definitions (CN/EN)
- Part of speech, example sentences with translations
- Audio file references, synonyms, antonyms
- HTML-to-structured-data extraction
"""

import re
import html
import struct
import zlib
import gzip
import json
from pathlib import Path
from typing import Generator, Optional


class MDXReader:
    """Read MDX dictionary files and yield word entries."""

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"MDX file not found: {filepath}")
        self._f = None
        self._header: dict = {}
        self._key_block_offsets: list = []
        self._record_block_offsets: list = []
        self._encoding: str = "utf-8"

    def __enter__(self):
        self._f = open(self.filepath, "rb")
        self._parse_header()
        return self

    def __exit__(self, *args):
        if self._f:
            self._f.close()

    def _parse_header(self):
        f = self._f
        magic = f.read(4)
        if magic != b"MDX\x00":
            raise ValueError(f"Not a valid MDX file (magic: {magic!r})")
        header_size = struct.unpack(">I", f.read(4))[0]
        header_compressed = f.read(header_size)
        try:
            header_xml = gzip.decompress(header_compressed).decode("utf-8", errors="replace")
        except Exception:
            try:
                header_xml = header_compressed.decode("utf-8", errors="replace")
            except Exception:
                header_xml = header_compressed.decode("utf-16", errors="replace")

        self._header = {}
        for match in re.finditer(r'(\w+)="([^"]*)"', header_xml):
            self._header[match.group(1)] = match.group(2)

        enc = self._header.get("Encoding", "UTF-8").upper()
        encoding_map = {"UTF-8": "utf-8", "UTF8": "utf-8", "UTF-16": "utf-16-le", "UTF-16LE": "utf-16-le", "GBK": "gbk", "GB2312": "gbk"}
        self._encoding = encoding_map.get(enc, "utf-8")

        # Read key blocks
        num_key_blocks = struct.unpack(">Q", f.read(8))[0]
        self._key_block_offsets = []
        for _ in range(num_key_blocks):
            comp_size, decomp_size = struct.unpack(">QQ", f.read(16))
            offset = f.tell()
            self._key_block_offsets.append((offset, comp_size, decomp_size))
            f.seek(comp_size, 1)

        # Read record blocks
        num_record_blocks = struct.unpack(">Q", f.read(8))[0]
        self._record_block_offsets = []
        for _ in range(num_record_blocks):
            comp_size, decomp_size = struct.unpack(">QQ", f.read(16))
            offset = f.tell()
            self._record_block_offsets.append((offset, comp_size, decomp_size))
            f.seek(comp_size, 1)

    def _decompress_block(self, block_offsets: list, block_index: int) -> bytes:
        offset, comp_size, _ = block_offsets[block_index]
        self._f.seek(offset)
        data = self._f.read(comp_size)
        try:
            return zlib.decompress(data)
        except Exception:
            return data

    def _parse_entries_from_block(self, block_idx: int) -> list[dict]:
        entries = []
        try:
            key_data = self._decompress_block(self._key_block_offsets, block_idx)
            rec_data = self._decompress_block(self._record_block_offsets, block_idx)
        except Exception:
            return entries

        if len(key_data) < 8 or len(rec_data) < 8:
            return entries

        # Parse key block: num_entries + (offset, keyword_text)*
        kp, rp = 0, 0
        num_keys = struct.unpack(">Q", key_data[kp:kp + 8])[0]
        kp += 8
        rec_num = struct.unpack(">Q", rec_data[rp:rp + 8])[0]
        rp += 8

        # Extract keywords and definitions
        keywords = []
        for _ in range(min(num_keys, 500000)):
            if kp + 8 > len(key_data):
                break
            kw_offset = struct.unpack(">Q", key_data[kp:kp + 8])[0]
            kp += 8
            # Find null-terminated keyword
            kw_end = key_data.find(b"\x00", kw_offset)
            if kw_end == -1:
                kw_end = len(key_data)
            kw_bytes = key_data[kw_offset:kw_end]
            try:
                kw = kw_bytes.decode(self._encoding, errors="replace").strip()
            except Exception:
                kw = kw_bytes.decode("utf-8", errors="replace").strip()
            if kw:
                keywords.append(kw)

        definitions = []
        for _ in range(min(rec_num, 500000)):
            if rp + 4 > len(rec_data):
                break
            def_size = struct.unpack(">I", rec_data[rp:rp + 4])[0]
            rp += 4
            if rp + def_size > len(rec_data):
                break
            def_bytes = rec_data[rp:rp + def_size]
            rp += def_size
            try:
                def_text = def_bytes.decode(self._encoding, errors="replace")
            except Exception:
                def_text = def_bytes.decode("utf-8", errors="replace")
            definitions.append(def_text)

        for i in range(min(len(keywords), len(definitions))):
            entries.append({"word": keywords[i], "definition": definitions[i]})

        return entries

    def entries(self) -> Generator[dict, None, None]:
        for block_idx in range(len(self._key_block_offsets)):
            try:
                yield from self._parse_entries_from_block(block_idx)
            except Exception:
                continue


# ═══════════════════════════════════════════════════════
#  Enhanced HTML/Text Parser for Dictionary Entries
# ═══════════════════════════════════════════════════════

def clean_html(raw: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", "", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_phonetics(definition: str) -> tuple:
    """Extract US and UK phonetic transcriptions."""
    us_phonetic = ""
    uk_phonetic = ""

    # Pattern: UK /.../  US /.../
    uk_match = re.search(r"(?:UK|BrE|Br|英)\s*[/\[](.*?)[/\]]", definition, re.IGNORECASE)
    us_match = re.search(r"(?:US|AmE|Am|美|NAmE)\s*[/\[](.*?)[/\]]", definition, re.IGNORECASE)

    if uk_match:
        uk_phonetic = f"/{uk_match.group(1)}/"
    if us_match:
        us_phonetic = f"/{us_match.group(1)}/"

    # Fallback: generic phonetic
    if not us_phonetic and not uk_phonetic:
        match = re.search(r"[/\[]([a-zA-Zɪæɑɔəɛʌʊɒθðʃʒŋɡɹɜɒ̃ɛəɔ̃]+?)[/\]]", definition)
        if match:
            ph = f"/{match.group(1)}/"
            us_phonetic = uk_phonetic = ph

    return us_phonetic, uk_phonetic


def extract_part_of_speech(definition: str) -> str:
    """Extract part of speech from definition."""
    pos_patterns = [
        (r"\b(noun|verb|adjective|adverb|preposition|conjunction|pronoun|interjection|determiner|auxiliary|modal)\b\.?", 1),
        (r"\b(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|int\.|det\.|aux\.)\b", 0),
        (r"【([^】]+)】", 1),
        (r"〔([^〕]+)〕", 1),
    ]
    for pattern, group in pos_patterns:
        match = re.search(pattern, definition, re.IGNORECASE)
        if match:
            pos = match.group(group).strip().rstrip(".")
            pos_map = {
                "n": "noun", "v": "verb", "adj": "adjective", "adv": "adverb",
                "prep": "preposition", "conj": "conjunction", "pron": "pronoun",
            }
            return pos_map.get(pos.lower(), pos.lower())
    return ""


def extract_definitions(definition: str) -> tuple:
    """Extract Chinese and English definitions."""
    cn_parts = re.findall(r"[一-鿿]+[。，；\s]*[一-鿿一-鿿\s。，；]*", definition)
    chinese_def = "；".join(p for p in cn_parts if len(p) > 2)[:500] if cn_parts else ""

    # English definition: remove Chinese chunks
    clean = clean_html(definition)
    en_parts = re.split(r"[一-鿿一-鿿]+", clean)
    en_parts = [p.strip() for p in en_parts if len(p.strip()) > 5 and not re.match(r"^[/\[]", p.strip())]
    english_def = en_parts[0][:500] if en_parts else ""

    return chinese_def, english_def


def extract_examples(definition: str) -> list[dict]:
    """Extract example sentences with translations."""
    examples = []

    # Pattern: "Example sentence" → "translation"
    pairs = re.findall(
        r'(?:e\.g\.|eg\.|例如|例句[:：]?)?\s*["“]([^"”]{10,200})["”]\s*(?:[→→]\s*["“]?([^"”]{2,200})["”]?)?',
        definition, re.IGNORECASE
    )

    for en, cn in pairs[:8]:
        en_clean = clean_html(en)[:250]
        cn_clean = clean_html(cn)[:250] if cn else ""
        if en_clean:
            examples.append({"en": en_clean, "cn": cn_clean})

    # Fallback: single quoted sentences
    if not examples:
        quotes = re.findall(r'["“]([^"”]{15,200})["”]', definition)
        for q in quotes[:5]:
            cleaned = clean_html(q)[:250]
            if cleaned:
                examples.append({"en": cleaned, "cn": ""})

    return examples


def extract_synonyms_antonyms(definition: str) -> tuple:
    """Extract synonyms and antonyms from definition."""
    synonyms = ""
    antonyms = ""

    syn_match = re.search(r"(?:synonyms?|SYN|近义词?|同义词?)[:：]?\s*([^.。\n]+)", definition, re.IGNORECASE)
    ant_match = re.search(r"(?:antonyms?|ANT|反义词?)[:：]?\s*([^.。\n]+)", definition, re.IGNORECASE)

    if syn_match:
        synonyms = clean_html(syn_match.group(1))[:300]
    if ant_match:
        antonyms = clean_html(ant_match.group(1))[:300]

    # Also parse from structured formats like "OPP: xxx"
    if not antonyms:
        opp_match = re.search(r"(?:OPP|opposite?)[:：]?\s*([^.。\n]+)", definition, re.IGNORECASE)
        if opp_match:
            antonyms = clean_html(opp_match.group(1))[:300]

    return synonyms, antonyms


def extract_audio_refs(definition: str) -> tuple:
    """Extract audio file references from definition."""
    us_audio = ""
    uk_audio = ""

    # Look for audio href/src patterns
    audio_patterns = [
        r'href="([^"]*\.(?:mp3|wav|ogg|spx|m4a)[^"]*)"',
        r'src="([^"]*\.(?:mp3|wav|ogg|spx|m4a)[^"]*)"',
        r'sound://([^\s<]+)',
    ]

    for pattern in audio_patterns:
        matches = re.findall(pattern, definition, re.IGNORECASE)
        for m in matches:
            lower = m.lower()
            if "us" in lower or "ame" in lower:
                us_audio = m
            elif "uk" in lower or "bre" in lower:
                uk_audio = m
            elif not us_audio:
                us_audio = m

    return us_audio, uk_audio


def parse_mdx_entry(definition: str) -> dict:
    """Parse a raw MDX definition into a structured dictionary entry."""
    us_ph, uk_ph = extract_phonetics(definition)
    pos = extract_part_of_speech(definition)
    cn_def, en_def = extract_definitions(definition)
    examples = extract_examples(definition)
    synonyms, antonyms = extract_synonyms_antonyms(definition)
    us_audio, uk_audio = extract_audio_refs(definition)

    return {
        "phonetic_us": us_ph or uk_ph or "",
        "phonetic_uk": uk_ph or us_ph or "",
        "definition_cn": cn_def,
        "definition_en": en_def,
        "part_of_speech": pos,
        "examples": examples,
        "synonyms": synonyms,
        "antonyms": antonyms,
        "audio_us": us_audio,
        "audio_uk": uk_audio,
    }


def import_mdx_to_db(filepath: str | Path, db_session_factory, book_id: int = 0) -> dict:
    """Import an MDX dictionary into the database.

    Args:
        filepath: Path to .mdx file
        db_session_factory: Callable that returns a new DB session
        book_id: Book ID to associate entries with

    Returns:
        dict with import statistics
    """
    from models import DictionaryEntry
    path = Path(filepath)
    stats = {"total": 0, "imported": 0, "skipped": 0, "errors": 0}

    db = db_session_factory()
    try:
        with MDXReader(path) as reader:
            batch = []
            for entry in reader.entries():
                stats["total"] += 1
                try:
                    parsed = parse_mdx_entry(entry["definition"])

                    dict_entry = DictionaryEntry(
                        book_id=book_id,
                        word=entry["word"],
                        phonetic=parsed["phonetic_us"] or parsed["phonetic_uk"] or "",
                        definition_cn=parsed["definition_cn"],
                        definition_en=parsed["definition_en"],
                        part_of_speech=parsed["part_of_speech"],
                        example=json.dumps(parsed["examples"], ensure_ascii=False) if parsed["examples"] else "",
                        example_translation="",
                        audio_us=parsed["audio_us"],
                        audio_uk=parsed["audio_uk"],
                        synonyms=parsed["synonyms"],
                        antonyms=parsed["antonyms"],
                        source=path.name,
                    )
                    batch.append(dict_entry)
                    stats["imported"] += 1

                    if len(batch) >= 200:
                        db.add_all(batch)
                        db.commit()
                        batch = []
                except Exception:
                    stats["errors"] += 1

            if batch:
                db.add_all(batch)
                db.commit()
    except Exception as e:
        stats["error_message"] = str(e)
    finally:
        db.close()
    return stats

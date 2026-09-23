"""Audio service — Microsoft Edge Neural TTS with local caching.

Voices:
  en-US-JennyNeural  — American female (default)
  en-US-GuyNeural    — American male
  en-GB-SoniaNeural  — British female

Supports SSML prosody rate for speed control: 0.5x / 0.75x / 1.0x / 1.25x
Audio is cached as MP3 files in APPDATA/WordMaster/audio_cache/.
"""

import os
import io
import logging
import hashlib
import asyncio
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Voice configuration
VOICES = {
    "us": {"name": "en-US-JennyNeural", "label": "American Female"},
    "us-male": {"name": "en-US-GuyNeural", "label": "American Male"},
    "uk": {"name": "en-GB-SoniaNeural", "label": "British Female"},
}

# Speed → SSML rate mapping
SPEED_RATES = {
    0.50: "x-slow",
    0.75: "slow",
    1.00: "medium",
    1.25: "fast",
}

# Cache directory
if os.name == 'nt':
    CACHE_DIR = Path(os.getenv('APPDATA', Path.home() / 'AppData' / 'Roaming')) / 'WordMaster' / 'audio_cache'
else:
    CACHE_DIR = Path.home() / '.cache' / 'wordmaster' / 'audio'

CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(word: str, voice_key: str, speed: float) -> Path:
    """Build cache file path for given word + voice + speed."""
    raw = f"{word.lower()}:{voice_key}:{speed}".encode()
    name = hashlib.md5(raw).hexdigest() + ".mp3"
    return CACHE_DIR / name


def _build_ssml(text: str, voice_key: str, speed: float) -> str:
    """Build SSML string for Edge TTS."""
    voice = VOICES.get(voice_key, VOICES["us"])
    rate = SPEED_RATES.get(speed, "medium")
    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">'
        f'<voice name="{voice["name"]}">'
        f'<prosody rate="{rate}">'
        f'{text}'
        f'</prosody>'
        f'</voice>'
        f'</speak>'
    )


async def generate_audio(
    text: str,
    voice_key: str = "us",
    speed: float = 1.0,
) -> Optional[bytes]:
    """Generate MP3 audio using Edge TTS and cache locally.

    Args:
        text: Text to speak (word or sentence).
        voice_key: "us" | "us-male" | "uk"
        speed: 0.50 | 0.75 | 1.00 | 1.25

    Returns:
        MP3 audio bytes, or None on failure.
    """
    if not text or not text.strip():
        return None

    text = text.strip()
    cache_file = _cache_path(text, voice_key, speed)

    # ── Return cached ──
    if cache_file.exists():
        logger.debug(f"Audio cache hit: {text} ({voice_key}@{speed}x)")
        return cache_file.read_bytes()

    # ── Generate via Edge TTS ──
    try:
        import edge_tts

        ssml = _build_ssml(text, voice_key, speed)
        communicate = edge_tts.Communicate(ssml)

        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

        if not chunks:
            logger.warning(f"Edge TTS returned no audio for '{text}'")
            return None

        audio_bytes = b"".join(chunks)
        cache_file.write_bytes(audio_bytes)
        logger.info(f"Audio cached: {text} ({voice_key}@{speed}x) → {cache_file.name} ({len(audio_bytes)} bytes)")
        return audio_bytes

    except ImportError:
        logger.error("edge-tts not installed. Run: pip install edge-tts")
        return None
    except Exception as e:
        logger.error(f"Edge TTS generation failed for '{text}': {type(e).__name__}: {e}")
        return None


def get_cached_audio(text: str, voice_key: str = "us", speed: float = 1.0) -> Optional[bytes]:
    """Get cached audio bytes synchronously. Returns None if not cached."""
    cache_file = _cache_path(text, voice_key, speed)
    if cache_file.exists():
        return cache_file.read_bytes()
    return None


def is_cached(text: str, voice_key: str = "us", speed: float = 1.0) -> bool:
    """Check if audio is already cached."""
    return _cache_path(text, voice_key, speed).exists()


def clear_audio_cache() -> dict:
    """Clear all cached audio files. Returns stats."""
    files = list(CACHE_DIR.glob("*.mp3"))
    total_bytes = sum(f.stat().st_size for f in files)
    count = len(files)
    for f in files:
        try:
            f.unlink()
        except Exception:
            pass
    logger.info(f"Audio cache cleared: {count} files, {total_bytes} bytes")
    return {"deleted": count, "bytes_freed": total_bytes}


def cache_stats() -> dict:
    """Get cache statistics."""
    files = list(CACHE_DIR.glob("*.mp3"))
    total_bytes = sum(f.stat().st_size for f in files)
    return {
        "files": len(files),
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "directory": str(CACHE_DIR),
    }


def list_voices() -> list[dict]:
    """List available TTS voices."""
    return [
        {"key": k, "name": v["name"], "label": v["label"]}
        for k, v in VOICES.items()
    ]

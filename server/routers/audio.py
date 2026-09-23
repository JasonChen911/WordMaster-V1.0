"""Audio routes: Edge Neural TTS voices, cache management, word audio."""

from fastapi import APIRouter, Query
from fastapi.responses import Response as FastAPIResponse, JSONResponse

from audio_service import (
    generate_audio, get_cached_audio, is_cached,
    clear_audio_cache, cache_stats, list_voices,
)

router = APIRouter()


@router.get("/api/audio/voices")
def get_voices():
    """List available Edge Neural TTS voices."""
    return {"voices": list_voices(), "default": "us"}


@router.get("/api/audio/cache/stats")
def get_cache_stats():
    """Get audio cache statistics."""
    return cache_stats()


@router.delete("/api/audio/cache")
def delete_audio_cache():
    """Clear all cached audio files."""
    result = clear_audio_cache()
    return {"cleared": True, **result}


@router.get("/api/audio/{word}")
async def get_word_audio(
    word: str,
    voice: str = Query("us", description="us | us-male | uk"),
    speed: float = Query(1.0, ge=0.5, le=1.25, description="0.5 | 0.75 | 1.0 | 1.25"),
):
    """Generate and return MP3 audio for a word using Microsoft Edge Neural TTS."""
    # Skip non-word route segments (safety net)
    if word in ("voices", "cache", "status"):
        return JSONResponse({"error": "Invalid word"}, status_code=400)

    supported = [0.5, 0.75, 1.0, 1.25]
    speed_val = min(supported, key=lambda x: abs(x - speed))

    # Check cache first
    cached = get_cached_audio(word, voice, speed_val)
    if cached is not None:
        return FastAPIResponse(content=cached, media_type="audio/mpeg",
                               headers={"X-Audio-Source": "cache", "Cache-Control": "public, max-age=86400"})

    # Generate via Edge TTS
    audio_bytes = await generate_audio(word, voice_key=voice, speed=speed_val)
    if audio_bytes is None:
        return JSONResponse(
            {"error": "TTS generation failed. Make sure edge-tts is installed."},
            status_code=500,
        )

    return FastAPIResponse(content=audio_bytes, media_type="audio/mpeg",
                           headers={"X-Audio-Source": "generated", "Cache-Control": "public, max-age=86400"})


@router.get("/api/audio/{word}/status")
def get_audio_status(word: str, voice: str = "us", speed: float = 1.0):
    """Check if audio is cached for a word."""
    supported = [0.5, 0.75, 1.0, 1.25]
    speed_val = min(supported, key=lambda x: abs(x - speed))
    return {
        "word": word,
        "voice": voice,
        "speed": speed_val,
        "cached": is_cached(word, voice, speed_val),
    }

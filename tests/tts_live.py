"""Explicit live-network regression: inspect provider boundary text and audio."""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import audio_service
import edge_tts

WORDS = ['telegram', 'abandon', 'apple', 'book', 'computer', 'dictionary', 'English', 'learn', 'school', 'voice']

async def main():
    cache = Path(__file__).resolve().parents[1] / '.testdata' / 'tts-live'
    cache.mkdir(parents=True, exist_ok=True)
    original = edge_tts.Communicate.stream
    results = []
    async def stream(client):
        async for chunk in original(client):
            if chunk['type'] in ('WordBoundary', 'SentenceBoundary'):
                boundaries.append(chunk['text'])
            yield chunk
    with patch.object(audio_service, 'CACHE_DIR', cache), patch.object(edge_tts.Communicate, 'stream', stream):
        for word in WORDS:
            boundaries = []
            audio = None
            for attempt in range(3):
                audio = await audio_service.generate_audio(word)
                if audio:
                    break
                print(f"Retry {word}: {attempt + 1}", flush=True)
            assert audio and len(audio) > 1000, word
            if boundaries:
                assert ' '.join(boundaries).lower() == word.lower(), (word, boundaries)
            assert audio_service.get_cached_audio(word) == audio
            results.append({'word': word, 'bytes': len(audio), 'provider_spoken_text': boundaries, 'cache': 'verified'})
            print(json.dumps(results[-1]), flush=True)
    (cache / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')

asyncio.run(main())

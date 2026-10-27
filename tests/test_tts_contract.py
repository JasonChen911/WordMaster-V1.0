import hashlib
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import audio_service
import edge_tts


class TTSContract(unittest.TestCase):
    def test_provider_receives_only_word(self):
        original = edge_tts.Communicate
        captured = []

        def capture(text, *args, **kwargs):
            captured.append((text, kwargs, b''.join(original(text, *args, **kwargs).texts).decode()))
            raise RuntimeError('Stop before network')

        with tempfile.TemporaryDirectory() as directory, patch.object(audio_service, 'CACHE_DIR', Path(directory)), patch.object(edge_tts, 'Communicate', capture):
            asyncio.run(audio_service.generate_audio('telegram'))
        self.assertEqual(captured[0][0], 'telegram')
        self.assertEqual(captured[0][2], 'telegram')
        self.assertEqual(captured[0][1]['voice'], 'en-US-JennyNeural')

    def test_cache_version(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(audio_service, 'CACHE_DIR', Path(directory)):
            old = Path(directory) / (hashlib.md5(b'v3:telegram:us:1.0').hexdigest() + '.mp3')
            old.write_bytes(b'old audio speaking SSML URL')
            self.assertIsNone(audio_service.get_cached_audio('telegram'))


if __name__ == '__main__':
    unittest.main()

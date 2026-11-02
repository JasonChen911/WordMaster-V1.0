"""Regression tests for bounded storage and local API access."""
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT))
os.environ["WORDMASTER_DATA_DIR"] = tempfile.mkdtemp(prefix="wm-maintenance-")


class StorageTests(unittest.TestCase):
    def test_loopback_probe_does_not_initialize_https(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from threading import Thread
        from unittest.mock import patch
        from main import loopback_get

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ready")

            def log_message(self, *_args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch("ssl.create_default_context", side_effect=FileNotFoundError("SSL unavailable")):
                self.assertEqual(loopback_get(server.server_port, "/health", 2), (200, b"ready"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_webview_profile_does_not_depend_on_port(self):
        from main import webview_storage_path
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(webview_storage_path(Path(directory)), Path(directory) / "webview" / "profile")

    def test_backup_is_consistent_with_uncheckpointed_wal(self):
        from backup_utils import create_sqlite_backup
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "data.db"
            writer = sqlite3.connect(source)
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("CREATE TABLE items (value TEXT)")
            writer.execute("INSERT INTO items VALUES ('latest')")
            writer.commit()
            backup = Path(directory) / "backup.db"
            create_sqlite_backup(source, backup)
            with closing(sqlite3.connect(backup)) as reader:
                self.assertEqual(reader.execute("SELECT value FROM items").fetchone()[0], "latest")
            writer.close()

    def test_current_schema_does_not_trigger_daily_backup(self):
        from backup_utils import needs_upgrade_backup
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "data.db"
            with closing(sqlite3.connect(source)) as db:
                db.execute("CREATE TABLE schema_version (version TEXT)")
                db.execute("INSERT INTO schema_version VALUES ('v15.0_mistake_records')")
                db.execute("CREATE TABLE user_settings (key TEXT, value TEXT)")
                db.execute("INSERT INTO user_settings VALUES ('builtin_books_version', '2026.09.21')")
                db.execute("CREATE TABLE words (english TEXT)")
                db.commit()
            self.assertFalse(needs_upgrade_backup(source, "v15.0_mistake_records", "2026.09.21"))
            self.assertTrue(needs_upgrade_backup(source, "v16.0", "2026.09.21"))
            with closing(sqlite3.connect(source)) as db:
                db.executemany("INSERT INTO words VALUES (?)", [("Apple",), ("apple",)])
                db.commit()
            self.assertTrue(needs_upgrade_backup(source, "v15.0_mistake_records", "2026.09.21"))

    def test_audio_cache_prunes_oldest_to_budget(self):
        from audio_service import prune_audio_cache
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / "old.mp3"; old.write_bytes(b"a" * 8)
            new = root / "new.mp3"; new.write_bytes(b"b" * 8)
            os.utime(old, (1, 1))
            prune_audio_cache(root, max_bytes=8)
            self.assertFalse(old.exists())
            self.assertTrue(new.exists())

    def test_audio_cache_hit_refreshes_last_use(self):
        from audio_service import _cache_path, get_cached_audio
        from unittest.mock import patch
        import audio_service
        with tempfile.TemporaryDirectory() as directory, patch.object(audio_service, "CACHE_DIR", Path(directory)):
            cached = _cache_path("apple", "us", 1.0)
            cached.write_bytes(b"audio")
            os.utime(cached, (1, 1))
            self.assertEqual(get_cached_audio("apple"), b"audio")
            self.assertGreater(cached.stat().st_atime, 1)


class LocalAccessTests(unittest.TestCase):
    def test_foreign_origin_and_host_are_rejected(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from local_access import LocalAccessMiddleware
        app = FastAPI()
        app.add_middleware(LocalAccessMiddleware)

        @app.post("/api/change")
        def change():
            return {"ok": True}

        client = TestClient(app, base_url="http://127.0.0.1:8000")
        self.assertEqual(client.post("/api/change", headers={"origin": "http://evil.example"}).status_code, 403)
        self.assertEqual(client.post("/api/change", headers={"host": "evil.example"}).status_code, 403)
        self.assertEqual(client.post("/api/change", headers={"origin": "http://127.0.0.1:8000"}).status_code, 200)
        remote = TestClient(app, base_url="http://testserver", client=("192.0.2.1", 1234))
        self.assertEqual(remote.post("/api/change").status_code, 403)


if __name__ == "__main__":
    unittest.main()

import os
import sys
import tempfile
import unittest
import json
import hashlib
from pathlib import Path
_data = tempfile.TemporaryDirectory(prefix='wm-assets-')
os.environ['WORDMASTER_DATA_DIR'] = _data.name
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))


class FrontendBundleTest(unittest.TestCase):
    def fixture(self, root):
        (root / 'assets').mkdir()
        files = {'assets/main-a.js': b'import("./Page-a.js")', 'assets/Page-a.js': b'export default 1'}
        for name, data in files.items():
            (root / name).write_bytes(data)
        index = b'<meta name="wordmaster-build" content="test-a"><script type="module" src="/assets/main-a.js"></script>'
        (root / 'index.html').write_bytes(index)
        (root / 'build-test-a.json').write_text(json.dumps({'build_id':'test-a','files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}, 'index_sha256':hashlib.sha256(index).hexdigest()}))

    def test_snapshot_survives_live_rebuild(self):
        from frontend_assets import FrontendBundle
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            bundle = FrontendBundle(root)
            (root / 'assets/Page-a.js').unlink()
            (root / 'index.html').write_text('new build')
            self.assertEqual(bundle.files['assets/Page-a.js'], b'export default 1')
            self.assertIn(b'test-a', bundle.files['index.html'])

    def test_corrupt_or_missing_asset_fails_before_window(self):
        from frontend_assets import FrontendBundle
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            (root / 'assets/Page-a.js').write_text('corrupt')
            with self.assertRaisesRegex(RuntimeError, 'Page-a.js'):
                FrontendBundle(root)

    def test_http_cache_and_missing_asset(self):
        from frontend_assets import FrontendBundle, mount_frontend
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            app = FastAPI(); mount_frontend(app, FrontendBundle(root))
            with TestClient(app) as client:
                for route in ['/', '/study', '/index.html']:
                    self.assertIn('no-store', client.get(route).headers['cache-control'])
                self.assertIn('immutable', client.get('/assets/Page-a.js').headers['cache-control'])
                self.assertEqual(client.get('/assets/missing.js').status_code, 404)
                self.assertEqual(client.get('/missing.js').status_code, 404)

if __name__ == '__main__': unittest.main()

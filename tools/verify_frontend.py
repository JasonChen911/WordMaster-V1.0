"""Validate exact frontend generation, every manifest checksum and chunk reference."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from frontend_assets import FrontendBundle
bundle = FrontendBundle(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'web/dist')
print(f'PASS build={bundle.build_id} files={len(bundle.files)} bytes={sum(map(len, bundle.files.values()))}')

"""E2E test: all pages render after ErrorBoundary integration."""
import sys, os
sys.path.insert(0, 'server')

import logging
for name in ['app', 'httpx', 'sqlalchemy', 'uvicorn']:
    logging.getLogger(name).setLevel(logging.ERROR)

from app import app
from fastapi.testclient import TestClient

client = TestClient(app)
PASS = 0
FAIL = 0


def check(name, condition, detail=''):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f'  OK  {name}')
    else:
        FAIL += 1
        print(f'  FAIL  {name} | {detail}')


print()
print('=' * 60)
print('  C-4 ERROR BOUNDARY — E2E VERIFICATION')
print('=' * 60)

# 1. Frontend build exists
from pathlib import Path
dist_index = Path('web/dist/index.html')
check('dist/index.html exists', dist_index.exists())

# 2. Frontend serves
r = client.get('/')
check('Frontend serves 200', r.status_code == 200)
html = r.text
check('HTML has root div', 'id="root"' in html)
check('HTML has splash screen', 'id="splash"' in html)

# 3. JS bundle includes ErrorBoundary
import re
js_files = re.findall(r'/assets/index-[^"]+\.js', html)
check('JS bundle referenced', len(js_files) > 0, str(js_files))
if js_files:
    r = client.get(js_files[0])
    js_content = r.text
    check('ErrorBoundary in bundle', 'hasError' in js_content or 'ErrorBoundary' in js_content)
    check('ErrorFallback in bundle', '页面出现了问题' in js_content or 'ErrorFallback' in js_content)
    print(f'    Bundle size: {len(js_content)/1024:.0f} KB')

# 4. All pages serve HTML
pages = [
    ('Home (Dashboard)', '/'),
    ('Study', '/study'),
    ('Analytics', '/analytics'),
    ('Search', '/search'),
    ('Favorites', '/favorites'),
    ('Dictionary', '/dictionary'),
    ('Settings', '/settings'),
    ('AI Settings', '/settings/ai'),
    ('AI Tutor', '/ai-tutor'),
    ('Agreement', '/agreement'),
    ('About', '/about'),
]
print()
print('--- Page Serving ---')
for name, path in pages:
    r = client.get(path)
    ok = r.status_code == 200 and 'id="root"' in r.text
    check(f'{name} ({path})', ok, f'status={r.status_code}')

# 5. API endpoints still functional
print()
print('--- API Backend ---')
api_tests = [
    ('Dashboard', '/api/dashboard'),
    ('Study Queue', '/api/words/study-queue?count=3'),
    ('Books', '/api/books'),
    ('Stats', '/api/stats'),
    ('Search', '/api/search?q=test'),
    ('AI Config', '/api/ai/config-status'),
]
for name, path in api_tests:
    r = client.get(path)
    check(f'{name}', r.status_code == 200, f'{path} status={r.status_code}')

# 6. ErrorBoundary does NOT break existing behavior
# All pages return the same SPA HTML
r1 = client.get('/')
r2 = client.get('/study')
check('SPA: same root div on /', 'id="root"' in r1.text)
check('SPA: same root div on /study', 'id="root"' in r2.text)
check('SPA: JS bundle same', js_files[0] in r1.text and js_files[0] in r2.text)

# Summary
print()
print('=' * 60)
print(f'  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)')
if FAIL == 0:
    print('  C-4 COMPLETE — ErrorBoundary integrated')
else:
    print(f'  C-4: {FAIL} failures')
print('=' * 60)

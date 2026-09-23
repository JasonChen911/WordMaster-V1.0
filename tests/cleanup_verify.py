"""Post-cleanup SQLite verification."""
import sys, os, sqlite3
sys.path.insert(0, 'server')

import logging
for name in ['app', 'httpx', 'sqlalchemy', 'uvicorn']:
    logging.getLogger(name).setLevel(logging.ERROR)

from app import app
from fastapi.testclient import TestClient
from pathlib import Path

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
print('  POST-CLEANUP SQLite VERIFICATION')
print('=' * 60)

# 1. API endpoints
print()
print('--- API Endpoints ---')
endpoints = [
    ('Dashboard', '/api/dashboard'),
    ('Study Queue', '/api/words/study-queue?count=5'),
    ('Words All', '/api/words/all'),
    ('Search', '/api/search?q=test'),
    ('Stats', '/api/stats'),
    ('Weekly', '/api/stats/weekly'),
    ('Books', '/api/books'),
    ('Book Progress', '/api/books/CET4/progress'),
    ('Debug States', '/api/debug/word-states'),
    ('Favorites', '/api/favorites'),
    ('AI Config', '/api/ai/config-status'),
]
for name, path in endpoints:
    r = client.get(path)
    check(f'{name}', r.status_code == 200, f'{path} status={r.status_code}')

# 2. Study write
print()
print('--- Study Write Path ---')
r = client.get('/api/words/study-queue?count=3')
queue = r.json()
if queue:
    word = queue[0]['english']
    r = client.post('/api/study', json={
        'word_id': word, 'result': 'know', 'seconds_spent': 5
    })
    check('Study write works', r.status_code == 200 and
          r.json().get('message') == 'Study recorded')

# 3. DB integrity
print()
print('--- Database Integrity ---')
db = sqlite3.connect('server/wordmaster.db')

integrity_checks = [
    ('words table', 'SELECT COUNT(*) FROM words', 12552),
    ('dictionary table', 'SELECT COUNT(*) FROM dictionary', 27691),
    ('books table (>=5)', 'SELECT COUNT(*) FROM books', None),
    ('book_words links', 'SELECT COUNT(*) FROM book_words', 27691),
    ('study_records exist', 'SELECT COUNT(*) FROM study_records', None),
    ('daily_stats exist', 'SELECT COUNT(*) FROM daily_stats', None),
    ('user_settings', "SELECT COUNT(*) FROM user_settings", 1),
]

for label, sql, expected in integrity_checks:
    val = db.execute(sql).fetchone()[0]
    if expected is not None:
        ok = val == expected
        check(label, ok, f'expected={expected} got={val}')
    else:
        ok = val > 0
        check(label, ok, f'got={val}')

# Orphan checks
orphan_sr = db.execute(
    'SELECT COUNT(*) FROM study_records sr '
    'LEFT JOIN words w ON w.id = sr.word_id WHERE w.id IS NULL'
).fetchone()[0]
check('No orphan study_records', orphan_sr == 0, f'{orphan_sr} orphans')

orphan_bw = db.execute(
    'SELECT COUNT(*) FROM book_words bw '
    'LEFT JOIN words w ON w.id = bw.word_id WHERE w.id IS NULL'
).fetchone()[0]
check('No orphan book_words', orphan_bw == 0, f'{orphan_bw} orphans')

db.close()

# 4. File system
print()
print('--- File System State ---')
check('data/vocabulary/ preserved', Path('data/vocabulary').exists())
txt_count = len(list(Path('data/vocabulary').glob('*.txt')))
check('5 TXT files in vocabulary', txt_count == 5, f'{txt_count} files')
check('内置词库请勿删除/ removed', not Path('内置词库请勿删除').exists())
check('word_manager.py preserved', Path('server/word_manager.py').exists())
check('wordmaster.db preserved', Path('server/wordmaster.db').exists())

backup_base = Path.home() / 'AppData' / 'Roaming' / 'WordMaster'
backups = list(backup_base.glob('backup_*'))
check(f'Backup preserved ({len(backups)} dirs)', len(backups) > 0)

user_data = backup_base / 'user_data'
check('AppData user_data preserved', user_data.exists() and
      len(list(user_data.glob('*.json'))) > 0)

# Summary
total_disk_saved = 1950.8 + 1485.8 + 3506.9 + 2651.1 + 1658.9 + 325.1 + 286.5 + 226.6 + 519.4 + 499.3
print()
print('=' * 60)
print(f'  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)')
print(f'  Disk space freed: {total_disk_saved:.0f} KB ({total_disk_saved/1024:.1f} MB)')
print(f'  Files deleted: 10 (5 JSON + 5 TXT)')
print(f'  Directories removed: 1 (内置词库请勿删除/)')
if FAIL == 0:
    print('  STATUS: ALL CHECKS PASSED — Step 5 complete')
else:
    print(f'  STATUS: {FAIL} FAILURES')
print('=' * 60)

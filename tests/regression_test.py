"""WordMaster Comprehensive Regression Test Suite — All SQLite-backed."""
import sys, os, json, sqlite3
sys.path.insert(0, 'server')
os.environ['WORDMASTER_DATA_DIR'] = 'server'

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
        print(f'  FAIL  {name}  |  {detail}')


print()
print('=' * 70)
print('  WORDMASTER REGRESSION TEST SUITE (SQLite)')
print('=' * 70)

# ---- 1. Startup & Frontend ----
print()
print('--- 1. BACKEND STARTUP & FRONTEND ---')

r = client.get('/')
check('Frontend serves index.html', r.status_code == 200,
      f'status={r.status_code}')

r = client.get('/api/dashboard')
data = r.json()
check('Dashboard returns 200', r.status_code == 200)
check('Dashboard has total_words', 'total_words' in data)
check('Dashboard has active_book', 'active_book' in data)
check('Dashboard active_book not None', data['active_book'] is not None)
check('Dashboard total_words > 0', data['total_words'] > 0,
      f'total_words={data.get("total_words")}')
if data.get('active_book'):
    ab = data['active_book']
    print(f'    Active: {ab["id"]} ({ab["book_name"]}) '
          f'{ab["studied_count"]}/{ab["word_count"]} studied')

# ---- 2. Books ----
print()
print('--- 2. BOOK IMPORT & LISTING ---')

r = client.get('/api/books')
data = r.json()
books = data.get('books', [])
check('Books returns 200', r.status_code == 200)
check('Has 5 built-in books', len(books) >= 5, f'{len(books)} books')

for b in books:
    ok = b.get('word_count', 0) > 0
    check(f'  Book {b["id"]}: {b["word_count"]} words (builtin={b.get("is_builtin")})', ok)

r = client.get('/api/books/active')
check('Active book endpoint OK', r.status_code == 200)
ab = r.json().get('book', {})
check('Active book has id', 'id' in ab)
active_book_id = ab.get('id', 'CET4')
print(f'    Current active: {active_book_id}')

# Switch books test
r = client.post('/api/books/TOEFL/activate')
check('Switch to TOEFL success', r.json().get('success') == True,
      str(r.json()))
r = client.get('/api/books/active')
check('Now active is TOEFL', r.json()['book']['id'] == 'TOEFL')
# Restore original
client.post(f'/api/books/{active_book_id}/activate')
r = client.get('/api/books/active')
check('Restored active book', r.json()['book']['id'] == active_book_id)

# ---- 3. Study Flow ----
print()
print('--- 3. STUDY FLOW — Mark Words ---')

r = client.get('/api/words/study-queue?count=10')
queue = r.json()
check('Study queue returns list', isinstance(queue, list))
check('Study queue has 10 words', len(queue) == 10, f'{len(queue)} words')

if len(queue) >= 3:
    study_words = [
        (queue[0]['english'], 'know', 5),
        (queue[1]['english'], 'fuzzy', 3),
        (queue[2]['english'], 'unknown', 8),
    ]
    for word, result, secs in study_words:
        r = client.post('/api/study', json={
            'word_id': word, 'result': result, 'seconds_spent': secs
        })
        ok = (r.status_code == 200 and
              r.json().get('message') == 'Study recorded')
        resp = r.json()
        check(f'  Study "{word}" -> {result}', ok,
              f'status={r.status_code} resp={resp.get("message","?")}')
        if ok:
            w = resp['word']
            print(f'      proficiency={w["proficiency"]} '
                  f'next_review={str(w.get("next_review",""))[:19]}')

    # Verify first word updated in DB
    r = client.get(f'/api/search?q={study_words[0][0]}')
    results = r.json().get('words', [])
    matched = [w for w in results if w['english'] == study_words[0][0]]
    if matched:
        w = matched[0]
        check('Word study_status updated', w['study_status'] == 'learning',
              f'status={w["study_status"]}')
        check('Word review_count incremented', w['review_count'] > 0,
              f'rc={w["review_count"]}')
        check('Word proficiency updated', w['proficiency'] > 0,
              f'prof={w["proficiency"]}')
else:
    print('    (queue too small, skipping)')

# ---- 4. Statistics ----
print()
print('--- 4. STATISTICS & DASHBOARD ---')

r = client.get('/api/stats')
s = r.json()
check('Stats returns 200', r.status_code == 200)
check('Stats total_words > 0', s.get('total_words', 0) > 0)
check('Stats today_studied > 0', s.get('today_studied', 0) > 0,
      f'today_studied={s.get("today_studied")}')
check('Stats has proficiency_distribution',
      'proficiency_distribution' in s)
print(f'    today_studied={s.get("today_studied")} '
      f'mastered={s.get("total_mastered")} '
      f'accuracy={s.get("overall_accuracy")}')

r = client.get('/api/stats/weekly')
w_data = r.json()
check('Weekly stats returns 7 days', len(w_data) == 7,
      f'{len(w_data)} days')

r = client.get('/api/stats/errors')
check('Error words returns 200', r.status_code == 200)

r = client.get('/api/dashboard')
d = r.json()
check('Dashboard today_studied > 0', d.get('today_studied', 0) > 0)
check('Dashboard progress_percent float',
      isinstance(d.get('progress_percent'), (int, float)))

# ---- 5. Review Queue & Book Progress ----
print()
print('--- 5. REVIEW QUEUE & BOOK PROGRESS ---')

r = client.get('/api/words/today')
check('Today words returns list', isinstance(r.json(), list) and len(r.json()) > 0)

r = client.get(f'/api/books/{active_book_id}/progress')
p = r.json()
check('Book progress returns 200', r.status_code == 200)
check('Book progress studied > 0', p.get('studied_words', 0) > 0,
      f'studied={p.get("studied_words")}')
check('Book progress has percent',
      isinstance(p.get('progress_percent'), (int, float)))
print(f'    {active_book_id}: {p["studied_words"]}/{p["total_words"]} '
      f'studied ({p["progress_percent"]}%) '
      f' mastered={p["mastered_words"]} review_due={p["review_due"]}')

r = client.get('/api/debug/word-states')
ds = r.json()
counts = ds.get('counts', {})
total_check = (counts.get('new', 0) + counts.get('learning', 0) +
               counts.get('mastered', 0))
check('Debug new+learning+mastered=total',
      total_check == counts.get('total', -1),
      f'{total_check} vs {counts.get("total")}')
print(f'    new={counts["new"]} learning={counts["learning"]} '
      f'mastered={counts["mastered"]} review_due={counts["review_due"]}')

# ---- 6. Settings & AI Config ----
print()
print('--- 6. SETTINGS & AI CONFIG ---')

r = client.get('/api/ai/config-status')
ai = r.json()
check('AI config status 200', r.status_code == 200)
check('AI config has configured', 'configured' in ai)
check('AI config has api_base', 'api_base' in ai)
check('AI config NO key_preview (security fix)',
      'key_preview' not in ai,
      f'key_preview={ai.get("key_preview", "ABSENT")}')
check('AI config NO has_key (security fix)',
      'has_key' not in ai,
      f'has_key={ai.get("has_key", "ABSENT")}')
print(f'    configured={ai["configured"]} api_base={ai["api_base"]}')

# ---- 7. Data Integrity (Direct DB Check) ----
print()
print('--- 7. DATA INTEGRITY (SQLite) ---')

db = sqlite3.connect('server/wordmaster.db')

sr = db.execute('SELECT COUNT(*) FROM study_records').fetchone()[0]
check('study_records has entries', sr > 0, f'{sr} records')
print(f'    study_records: {sr} study events')

ds_cnt = db.execute('SELECT COUNT(*) FROM daily_stats').fetchone()[0]
check('daily_stats has entries', ds_cnt > 0, f'{ds_cnt} days')
print(f'    daily_stats: {ds_cnt} days tracked')

reviewed = db.execute(
    'SELECT COUNT(*) FROM words WHERE review_count > 0'
).fetchone()[0]
check('Words with review_count > 0', reviewed > 0, f'{reviewed} words')
print(f'    words reviewed: {reviewed} / '
      f'{db.execute("SELECT COUNT(*) FROM words").fetchone()[0]}')

st = db.execute(
    "SELECT value FROM user_settings WHERE key = 'active_book'"
).fetchone()
check('user_settings has active_book', st is not None)
valid_books = ['CET4', 'CET6', 'TOEFL', '考研', '高中']
check('active_book value valid',
      st[0] in valid_books if st else False,
      f'value={st[0] if st else "NONE"}')
print(f'    active_book setting: {st[0] if st else "NONE"}')

# Verify no orphan records
orphans = db.execute('''
    SELECT COUNT(*) FROM study_records sr
    LEFT JOIN words w ON w.id = sr.word_id
    WHERE w.id IS NULL
''').fetchone()[0]
check('No orphan study_records', orphans == 0, f'{orphans} orphans')

orphan_bw = db.execute('''
    SELECT COUNT(*) FROM book_words bw
    LEFT JOIN words w ON w.id = bw.word_id
    WHERE w.id IS NULL
''').fetchone()[0]
check('No orphan book_words', orphan_bw == 0, f'{orphan_bw} orphans')

# Check words with NULL fields (should be 0 after fix)
null_fields = db.execute('''
    SELECT COUNT(*) FROM words
    WHERE difficulty IS NULL OR review_count IS NULL
       OR proficiency IS NULL OR accuracy_rate IS NULL
''').fetchone()[0]
check('No NULL required fields in words', null_fields == 0,
      f'{null_fields} rows with NULL')

db.close()

# ---- 8. File Preservation ----
print()
print('--- 8. FILE PRESERVATION ---')

checks = [
    (Path.home() / 'AppData' / 'Roaming' / 'WordMaster' / 'user_data',
     'AppData user_data/'),
    (Path('内置词库请勿删除'), '内置词库请勿删除/'),
    (Path('server/_archived/word_manager.py'), 'word_manager.py'),
    (Path('data/vocabulary'), 'data/vocabulary/'),
]
for path, label in checks:
    exists = path.exists()
    check(f'{label} preserved', exists, 'MISSING')

# ---- 9. Search & Dictionary ----
print()
print('--- 9. SEARCH & DICTIONARY ---')

r = client.get('/api/search?q=abandon')
check('Search returns 200', r.status_code == 200)
check('Search finds abandon', len(r.json().get('words', [])) > 0)

r = client.get('/api/search/all?q=test')
check('Search/all returns 200', r.status_code == 200)
data = r.json()
check('Search/all has study_words', 'study_words' in data)
check('Search/all has dictionary_results', 'dictionary_results' in data)

r = client.get('/api/dictionary/search?q=abandon&limit=3')
check('Dictionary search OK', r.status_code == 200)

r = client.get('/api/favorites')
check('Favorites endpoint OK', r.status_code == 200)

r = client.get('/api/words/all')
check('Words/all returns 200 (moved before {word_id})',
      r.status_code == 200)
check('Words/all returns many words',
      len(r.json()) > 10000, f'{len(r.json())} words')

# ---- SUMMARY ----
print()
print('=' * 70)
print(f'  REGRESSION RESULT: {PASS} PASSED, {FAIL} FAILED  '
      f'({PASS + FAIL} total checks)')
if FAIL == 0:
    print('  STATUS: ALL CHECKS PASSED')
    print('  Ready for Step 5 (cleanup)')
else:
    print(f'  STATUS: {FAIL} FAILURES — fix before Step 5')
print('=' * 70)

sys.exit(0 if FAIL == 0 else 1)

import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from models import Word, Book, BookWord, WordMemoryState, MistakeRecord
from routers.mistakes import router
from core import _generate_study_queue_sql


class MistakeContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(self.tmp.name) / 'test.db'), connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            connection.execute(text('CREATE TABLE user_settings (key TEXT PRIMARY KEY, value TEXT)'))
        self.session = sessionmaker(bind=self.engine)
        app = FastAPI()
        app.include_router(router)
        def db():
            with self.session() as session:
                yield session
        app.dependency_overrides[get_db] = db
        self.client = TestClient(app)
        with self.session() as db:
            db.add(Word(id=1, english='English', chinese='英语', phonetic='', example_en='I learn English.', example_cn='我学习英语。', study_status='mastered', is_mastered=True, review_count=4, next_review=datetime.now()+timedelta(days=30)))
            db.add(Book(id=1, book_name='test'))
            db.add(BookWord(book_id=1, word_id=1))
            db.add(WordMemoryState(word_id=1, due=datetime.now()+timedelta(days=30), stability=50, reps=4))
            db.commit()

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        self.tmp.cleanup()

    def test_id_and_round_retry(self):
        payload = dict(word_id=1, source='game', mistake_type='spelling', session_id='round-1')
        for _ in range(3):
            self.assertEqual(self.client.post('/api/mistakes', json=payload).status_code, 200)
        rows = self.client.get('/api/mistakes?source=game').json()['mistakes']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['count'], 1)
        payload['session_id'] = 'round-2'
        self.client.post('/api/mistakes', json=payload)
        self.assertEqual(self.client.get('/api/mistakes').json()['mistakes'][0]['count'], 2)

    def test_legacy_case_and_dual_source(self):
        for source in ['daily', 'game']:
            self.client.post('/api/mistakes', json=dict(word='english', source=source))
        self.assertEqual(self.client.get('/api/mistakes/stats').json(), dict(total=1, daily=1, game=1))
        for source in ['daily', 'game']:
            rows = self.client.get('/api/mistakes?source='+source).json()['mistakes']
            self.assertEqual([r['source'] for r in rows], [source])

    def test_review_enters_existing_queue_without_fake_review(self):
        self.client.post('/api/mistakes/1/review')
        with self.session() as db:
            self.assertEqual([r['id'] for r in _generate_study_queue_sql(db, 1, 20)], [1])
            self.assertEqual(db.get(Word, 1).review_count, 4)
            mem = db.query(WordMemoryState).filter_by(word_id=1).one()
            self.assertLessEqual(mem.due, datetime.now())
            self.assertEqual(mem.stability, 50)
            self.assertEqual(mem.reps, 4)

    def test_invalid_request_is_not_success(self):
        self.assertGreaterEqual(self.client.post('/api/mistakes', json=[]).status_code, 400)
        self.assertEqual(self.client.post('/api/mistakes', json=dict(word_id=999, source='game')).status_code, 404)


if __name__ == '__main__':
    unittest.main()

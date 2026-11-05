"""Persistent AI reading generations, including their exact questions."""
import json
from datetime import datetime, timezone

from sqlalchemy import text
from database import engine


def _ensure_table(conn):
    conn.execute(text("""CREATE TABLE IF NOT EXISTS ai_reading_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        title TEXT NOT NULL,
        exam TEXT NOT NULL,
        level TEXT NOT NULL,
        topic TEXT NOT NULL,
        question_types TEXT NOT NULL,
        article_json TEXT NOT NULL
    )"""))


def save_reading(article, exam, level, topic):
    kinds = list(dict.fromkeys(q.get('type') or '选择题' for q in article.get('questions', [])))
    with engine.begin() as conn:
        _ensure_table(conn)
        row = conn.execute(text("""INSERT INTO ai_reading_history
            (created_at, title, exam, level, topic, question_types, article_json)
            VALUES (:created_at, :title, :exam, :level, :topic, :question_types, :article_json)"""), {
            'created_at': datetime.now(timezone.utc).isoformat(),
            'title': article.get('title') or topic,
            'exam': exam, 'level': level, 'topic': topic,
            'question_types': json.dumps(kinds, ensure_ascii=False),
            'article_json': json.dumps(article, ensure_ascii=False),
        })
        return row.lastrowid


def list_readings():
    with engine.begin() as conn:
        _ensure_table(conn)
        rows = conn.execute(text("""SELECT id, created_at, title, exam, level, topic,
            question_types FROM ai_reading_history ORDER BY id DESC""")).mappings().all()
        return [dict(row, question_types=json.loads(row['question_types'])) for row in rows]


def get_reading(reading_id):
    with engine.begin() as conn:
        _ensure_table(conn)
        row = conn.execute(text("SELECT article_json FROM ai_reading_history WHERE id=:id"), {'id': reading_id}).first()
        return json.loads(row[0]) if row else None


def delete_reading(reading_id, db_engine=engine):
    """Delete one generated reading and its saved questions."""
    with db_engine.begin() as conn:
        _ensure_table(conn)
        result = conn.execute(text("DELETE FROM ai_reading_history WHERE id=:id"), {'id': reading_id})
        return result.rowcount > 0

"""Local, persistent conversations for the three AI tutors."""

from datetime import datetime, timezone

from sqlalchemy import text
from database import engine

TUTORS = frozenset({"emma", "alex", "sophia"})
ROLES = frozenset({"user", "assistant"})


def _now():
    return datetime.now(timezone.utc).isoformat()


def _ensure_tables(conn):
    conn.execute(text("""CREATE TABLE IF NOT EXISTS ai_tutor_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tutor TEXT NOT NULL,
        title TEXT NOT NULL DEFAULT '新对话',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )"""))
    conn.execute(text("""CREATE TABLE IF NOT EXISTS ai_tutor_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(conversation_id) REFERENCES ai_tutor_conversations(id)
    )"""))
    conn.execute(text("""CREATE INDEX IF NOT EXISTS ix_ai_tutor_messages_conversation
        ON ai_tutor_messages(conversation_id, id)"""))
    conn.execute(text("""CREATE INDEX IF NOT EXISTS ix_ai_tutor_conversations_tutor
        ON ai_tutor_conversations(tutor, updated_at DESC)"""))


def list_conversations(tutor, db_engine=engine):
    if tutor not in TUTORS:
        raise ValueError("未知导师")
    with db_engine.begin() as conn:
        _ensure_tables(conn)
        rows = conn.execute(text("""SELECT id, tutor, title, created_at, updated_at
            FROM ai_tutor_conversations WHERE tutor=:tutor
            ORDER BY updated_at DESC, id DESC"""), {"tutor": tutor}).mappings().all()
        return [dict(row) for row in rows]


def create_conversation(tutor, db_engine=engine):
    if tutor not in TUTORS:
        raise ValueError("未知导师")
    now = _now()
    with db_engine.begin() as conn:
        _ensure_tables(conn)
        result = conn.execute(text("""INSERT INTO ai_tutor_conversations
            (tutor, title, created_at, updated_at)
            VALUES (:tutor, '新对话', :now, :now)"""), {"tutor": tutor, "now": now})
        return {"id": result.lastrowid, "tutor": tutor, "title": "新对话",
                "created_at": now, "updated_at": now}


def get_conversation(conversation_id, tutor, db_engine=engine):
    if tutor not in TUTORS:
        raise ValueError("未知导师")
    with db_engine.begin() as conn:
        _ensure_tables(conn)
        row = conn.execute(text("""SELECT id, tutor, title, created_at, updated_at
            FROM ai_tutor_conversations WHERE id=:id AND tutor=:tutor"""),
            {"id": conversation_id, "tutor": tutor}).mappings().first()
        if row is None:
            return None
        messages = conn.execute(text("""SELECT id, role, content, created_at
            FROM ai_tutor_messages WHERE conversation_id=:id ORDER BY id"""),
            {"id": conversation_id}).mappings().all()
        return dict(row, messages=[dict(message) for message in messages])


def append_message(conversation_id, tutor, role, content, db_engine=engine):
    if tutor not in TUTORS or role not in ROLES or not isinstance(content, str):
        raise ValueError("无效消息")
    content = content.strip()
    if not content or len(content) > 10000:
        raise ValueError("消息长度无效")
    now = _now()
    with db_engine.begin() as conn:
        _ensure_tables(conn)
        row = conn.execute(text("""SELECT id, title FROM ai_tutor_conversations
            WHERE id=:id AND tutor=:tutor"""),
            {"id": conversation_id, "tutor": tutor}).mappings().first()
        if row is None:
            return None
        result = conn.execute(text("""INSERT INTO ai_tutor_messages
            (conversation_id, role, content, created_at)
            VALUES (:id, :role, :content, :now)"""),
            {"id": conversation_id, "role": role, "content": content, "now": now})
        title = content[:28] if role == "user" and row["title"] == "新对话" else row["title"]
        conn.execute(text("""UPDATE ai_tutor_conversations
            SET title=:title, updated_at=:now WHERE id=:id"""),
            {"title": title, "now": now, "id": conversation_id})
        return {"id": result.lastrowid, "role": role, "content": content,
                "created_at": now, "title": title}


def delete_conversation(conversation_id, tutor, db_engine=engine):
    """Delete exactly one tutor's conversation and its messages atomically."""
    if tutor not in TUTORS:
        raise ValueError("未知导师")
    with db_engine.begin() as conn:
        _ensure_tables(conn)
        row = conn.execute(text("""SELECT id FROM ai_tutor_conversations
            WHERE id=:id AND tutor=:tutor"""),
            {"id": conversation_id, "tutor": tutor}).first()
        if row is None:
            return False
        conn.execute(text("DELETE FROM ai_tutor_messages WHERE conversation_id=:id"), {'id': conversation_id})
        conn.execute(text("DELETE FROM ai_tutor_conversations WHERE id=:id"), {'id': conversation_id})
        return True

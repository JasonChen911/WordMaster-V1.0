"""Conversation persistence and tutor isolation."""

import sys
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from tutor_history import (append_message, create_conversation,
                           delete_conversation, get_conversation, list_conversations)


class TutorHistoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_engine = create_engine(f"sqlite:///{Path(self.temp.name) / 'tutors.db'}")

    def tearDown(self):
        self.db_engine.dispose()
        self.temp.cleanup()

    def test_conversations_survive_reopen_and_are_separate_by_tutor(self):
        db_engine = self.db_engine
        first = create_conversation('emma', db_engine)
        second = create_conversation('emma', db_engine)
        other = create_conversation('alex', db_engine)
        append_message(first['id'], 'emma', 'user', 'How do I use abandon?', db_engine)
        append_message(first['id'], 'emma', 'assistant', 'Here is an example.', db_engine)
        append_message(second['id'], 'emma', 'user', 'What about grammar?', db_engine)

        self.assertEqual([item['id'] for item in list_conversations('emma', db_engine)], [second['id'], first['id']])
        self.assertEqual([item['id'] for item in list_conversations('alex', db_engine)], [other['id']])
        self.assertIsNone(get_conversation(first['id'], 'alex', db_engine))
        restored = get_conversation(first['id'], 'emma', db_engine)
        self.assertEqual(restored['title'], 'How do I use abandon?')
        self.assertEqual([message['role'] for message in restored['messages']], ['user', 'assistant'])
        self.assertEqual(restored['messages'][1]['content'], 'Here is an example.')

    def test_rejects_invalid_or_cross_tutor_messages(self):
        db_engine = self.db_engine
        conversation = create_conversation('sophia', db_engine)
        self.assertIsNone(append_message(conversation['id'], 'emma', 'user', 'hello', db_engine))
        with self.assertRaises(ValueError):
            append_message(conversation['id'], 'sophia', 'system', 'secret', db_engine)
        with self.assertRaises(ValueError):
            append_message(conversation['id'], 'sophia', 'user', '   ', db_engine)
        self.assertEqual(get_conversation(conversation['id'], 'sophia', db_engine)['messages'], [])

    def test_delete_removes_only_selected_tutors_thread_and_messages(self):
        db_engine = self.db_engine
        removed = create_conversation('emma', db_engine)
        kept = create_conversation('emma', db_engine)
        other = create_conversation('alex', db_engine)
        append_message(removed['id'], 'emma', 'user', 'Delete me', db_engine)
        append_message(kept['id'], 'emma', 'user', 'Keep me', db_engine)
        append_message(other['id'], 'alex', 'user', 'Keep Alex', db_engine)

        self.assertFalse(delete_conversation(removed['id'], 'alex', db_engine))
        self.assertTrue(delete_conversation(removed['id'], 'emma', db_engine))
        self.assertFalse(delete_conversation(removed['id'], 'emma', db_engine))
        self.assertIsNone(get_conversation(removed['id'], 'emma', db_engine))
        self.assertEqual([item['id'] for item in list_conversations('emma', db_engine)], [kept['id']])
        self.assertEqual(get_conversation(other['id'], 'alex', db_engine)['messages'][0]['content'], 'Keep Alex')
        with db_engine.connect() as conn:
            from sqlalchemy import text
            count = conn.execute(text('SELECT count(*) FROM ai_tutor_messages WHERE conversation_id=:id'),
                                 {'id': removed['id']}).scalar()
            self.assertEqual(count, 0)


if __name__ == '__main__':
    unittest.main()

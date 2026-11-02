import sys
import unittest
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from database import Base
from models import (Book, BookWord, LearningEvent, MistakeRecord, SourceDocument,
                    SourceWord, StudyRecord, Word, WordMemoryState)
from repair import repair_data


class DuplicateMergeTest(unittest.TestCase):
    def test_case_merge_preserves_progress_and_relations(self):
        engine = create_engine("sqlite:///:memory:")
        @event.listens_for(engine, "connect")
        def _foreign_keys(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            book = Book(book_name="Custom")
            first = Word(english="Apple", phonetic="", chinese="苹果", example_en="", example_cn="",
                         review_count=2, correct_count=1, is_favorite=True)
            second = Word(english="apple", phonetic="", chinese="苹果", example_en="", example_cn="",
                          review_count=3, correct_count=2)
            doc = SourceDocument(title="Reading")
            db.add_all([book, first, second, doc]); db.flush()
            first_id, second_id = first.id, second.id
            db.add_all([
                BookWord(book_id=book.id, word_id=first_id),
                BookWord(book_id=book.id, word_id=second_id),
                StudyRecord(word_id=first_id, book_id=book.id, result="know"),
                StudyRecord(word_id=second_id, book_id=book.id, result="unknown"),
                LearningEvent(word_id=second_id, activity_type="review"),
                WordMemoryState(word_id=first_id, reps=2, lapses=0, last_review=datetime(2026, 1, 1)),
                WordMemoryState(word_id=second_id, reps=3, lapses=1, last_review=datetime(2026, 1, 2)),
                MistakeRecord(word_id=first_id, source="daily", count=1),
                MistakeRecord(word_id=second_id, source="daily", count=2),
                SourceWord(word_id=first_id, source_document_id=doc.id),
                SourceWord(word_id=second_id, source_document_id=doc.id),
            ])
            db.commit()
            repair_data(db); db.commit()
            surviving = db.query(Word).one()
            self.assertEqual(surviving.review_count, 5)
            self.assertEqual(surviving.correct_count, 3)
            self.assertTrue(surviving.is_favorite)
            self.assertEqual(db.query(BookWord).count(), 1)
            self.assertEqual(db.query(StudyRecord).filter_by(word_id=surviving.id).count(), 2)
            self.assertEqual(db.query(LearningEvent).one().word_id, surviving.id)
            self.assertEqual(db.query(MistakeRecord).one().count, 3)
            self.assertEqual(db.query(WordMemoryState).one().reps, 5)
            self.assertEqual(db.query(SourceWord).count(), 1)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()

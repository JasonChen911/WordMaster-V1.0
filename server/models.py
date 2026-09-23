from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from database import Base


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    english = Column(String, nullable=False, unique=True)
    phonetic = Column(String, nullable=False)
    chinese = Column(String, nullable=False)
    example_en = Column(String, nullable=False)
    example_cn = Column(String, nullable=False)
    illustration = Column(String, default="")  # filename in resources/illustrations/

    # Spaced repetition (Ebbinghaus-based)
    difficulty = Column(Float, default=2.5)        # 1-5 scale
    next_review = Column(DateTime, default=func.now())
    review_count = Column(Integer, default=0)
    correct_count = Column(Float, default=0.0)     # float for "fuzzy" = 0.5
    review_stage = Column(Integer, default=0)      # Ebbinghaus stage 0-6
    last_reviewed_at = Column(DateTime, nullable=True)

    # Computed stats
    accuracy_rate = Column(Float, default=0.0)     # 0.0 - 1.0
    proficiency = Column(Integer, default=0)        # 0-5 mastery level

    # Status flags
    is_favorite = Column(Boolean, default=False)
    is_mastered = Column(Boolean, default=False)
    study_status = Column(String, default="new")  # "new" | "learning" | "review"

    # Timestamp
    created_at = Column(DateTime, default=func.now())

    def compute_accuracy(self):
        """Recalculate accuracy rate."""
        if self.review_count == 0:
            self.accuracy_rate = 0.0
        else:
            self.accuracy_rate = min(1.0, self.correct_count / self.review_count)

    def compute_proficiency(self):
        """Calculate proficiency level (0-5) from accuracy and stage."""
        if self.review_count == 0:
            self.proficiency = 0
        elif self.is_mastered:
            self.proficiency = 5
        else:
            # Weighted: accuracy (60%) + review_stage progress (40%)
            stage_score = min(1.0, self.review_stage / 6.0)
            raw = self.accuracy_rate * 0.6 + stage_score * 0.4
            self.proficiency = max(0, min(5, round(raw * 5)))


class StudyRecord(Base):
    __tablename__ = "study_records"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, nullable=False)
    book_id = Column(Integer, nullable=False, default=0, index=True)
    result = Column(String, nullable=False)  # "know", "fuzzy", "unknown"
    review_stage = Column(Integer, default=0)
    studied_at = Column(DateTime, default=func.now())


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False, unique=True)  # YYYY-MM-DD
    words_studied = Column(Integer, default=0)
    words_mastered = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    minutes_studied = Column(Integer, default=0)  # Total study time in minutes


class DictionaryEntry(Base):
    """Professional dictionary entry — full lexical data."""
    __tablename__ = "dictionary"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, nullable=False, index=True, default=0)
    word = Column(String, nullable=False, index=True)
    phonetic = Column(String, default="")
    definition_cn = Column(String, default="")
    definition_en = Column(String, default="")
    part_of_speech = Column(String, default="")
    example = Column(String, default="")
    example_translation = Column(String, default="")
    audio_us = Column(String, default="")
    audio_uk = Column(String, default="")
    synonyms = Column(String, default="")
    antonyms = Column(String, default="")
    illustration = Column(String, default="")
    source = Column(String, default="")

    created_at = Column(DateTime, default=func.now())


class Book(Base):
    """A dictionary book (e.g., CET-4, CET-6, custom MDX)."""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    book_name = Column(String, nullable=False)
    file_name = Column(String, default="")
    word_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=False)
    is_builtin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class BookWord(Base):
    """Many-to-many membership used to isolate deletion and progress by book."""
    __tablename__ = "book_words"
    __table_args__ = (
        UniqueConstraint("book_id", "word_id", name="uq_book_words_book_word"),
    )

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, index=True)


class WordAIExplanation(Base):
    """Cached AI-generated detailed explanations for individual words."""
    __tablename__ = "word_ai_explanations"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False, unique=True, index=True)
    explanation = Column(String, nullable=False)  # JSON string with structured explanation
    created_at = Column(DateTime, default=func.now())


class AIContentCache(Base):
    """Cached AI-generated content keyed by (word, level, exam_type).

    Stores example sentences (and later exercises/analysis) so a word is only
    generated once per difficulty level, then served from cache. Re-generation
    is user-triggered only.
    """
    __tablename__ = "ai_content_cache"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False, index=True)
    level = Column(String, default="CET4", index=True)   # 高中 / CET4 / CET6 / 考研 / TOEFL
    exam_type = Column(String, default="general")        # general / cet4 / cet6 / kaoyan / toefl
    content_type = Column(String, default="example")     # example | exercise | analysis
    payload = Column(String, nullable=False)             # JSON string
    model = Column(String, default="")
    version = Column(String, default="1")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("word", "level", "exam_type", "content_type", name="uq_ai_content_cache_key"),
    )


class ConfusionSet(Base):
    """A pair of commonly-confused words with a discrimination explanation."""
    __tablename__ = "confusion_sets"

    id = Column(Integer, primary_key=True, index=True)
    word_a = Column(String, nullable=False, index=True)
    word_b = Column(String, nullable=False, index=True)
    distinction_cn = Column(String, default="")   # 区别说明（中文）
    memory_tip_cn = Column(String, default="")    # 最短记忆方法（中文）
    example_en = Column(String, default="")       # 双词对比例句（英文，含两词）
    example_cn = Column(String, default="")
    mastered = Column(Boolean, default=False)
    source = Column(String, default="builtin")    # builtin | ai
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("word_a", "word_b", name="uq_confusion_pair"),
    )


class SourceDocument(Base):
    """A reading/learning material a vocabulary word was first encountered in."""
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(String, default="")   # optional full text (privacy: only if user adds)
    created_at = Column(DateTime, default=func.now())


class SourceWord(Base):
    """Links a word to the document/sentence where the user first saw it."""
    __tablename__ = "source_words"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, index=True)
    source_document_id = Column(Integer, ForeignKey("source_documents.id"), nullable=False, index=True)
    source_sentence = Column(String, default="")

    __table_args__ = (
        UniqueConstraint("word_id", "source_document_id", name="uq_source_word"),
    )


class Course(Base):
    """A teacher-authored course (Local Classroom MVP).

    Demo courses/classes are explicitly flagged ``is_demo`` so they are never
    presented as real user data.
    """
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    book_id = Column(Integer, nullable=True)   # optional linked word book
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class Student(Base):
    """A student in a local classroom (demo data is flagged ``is_demo``)."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    class_name = Column(String, default="Demo Class")
    is_demo = Column(Boolean, default=True)
    words_studied = Column(Integer, default=0)
    words_mastered = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    lapses = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class StudentWordStat(Base):
    """Per-student, per-word performance used to compute class weak points."""
    __tablename__ = "student_word_stats"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    word = Column(String, nullable=False, index=True)
    wrong_count = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)
    lapses = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("student_id", "word", name="uq_student_word"),
    )


class LearningEvent(Base):
    """A single, immutable, raw learning behavior record.

    This is the *fact* layer: it stores what actually happened (activity type,
    answer, rating, response time, FSRS before/after). AI insights are a
    separate *interpretation* layer and are never mixed into these rows.
    """
    __tablename__ = "learning_events"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, default=0, index=True)
    session_id = Column(String, default="", index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)

    # What kind of activity produced this event.
    activity_type = Column(String, nullable=False, index=True)
    # "new_word" | "review" | "meaning_choice" | "spelling" | "listening"
    # | "context_fill" | "confusion_test" | "reading_lookup" | "exercise"

    # Outcome.
    result = Column(String, default="")            # "correct" | "incorrect"
    rating = Column(String, default="")            # "again" | "hard" | "good" | "easy"
    response_time_ms = Column(Integer, default=0)

    user_answer = Column(String, default="")
    correct_answer = Column(String, default="")
    error_type = Column(String, default="")        # meaning|spelling|listening|context|confusion|timeout|none

    # Where the event came from.
    source_type = Column(String, default="")       # study|exercise|reading|confusion|material
    source_id = Column(Integer, default=0)

    # FSRS state snapshots (JSON strings).
    fsrs_before = Column(String, default="")
    fsrs_after = Column(String, default="")

    client_version = Column(String, default="")
    algorithm_version = Column(String, default="")

    created_at = Column(DateTime, default=func.now())


class MistakeRecord(Base):
    """An aggregated mistake-book entry: one row per (word, source).

    The same word can have two rows — one for daily review mistakes, one for
    spelling-game mistakes — so the source distinction is preserved while the
    book itself stays de-duplicated (count increments instead of piling rows).
    """
    __tablename__ = "mistake_records"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, index=True)
    source = Column(String, nullable=False, index=True)      # "daily" | "game"
    mistake_type = Column(String, default="")                # meaning | spelling | ...
    count = Column(Integer, default=1)
    first_occurred_at = Column(DateTime, default=func.now())
    last_occurred_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_session_id = Column(String, default="")

    __table_args__ = (
        UniqueConstraint("word_id", "source", name="uq_mistake_word_source"),
    )


class WordMemoryState(Base):
    """FSRS adaptive memory state for a single word (one-to-one with ``words``).

    ``due`` is the single source of truth for when the word is next due for
    review. The older Ebbinghaus columns on ``words`` remain only for backward
    compatibility and coarse stats; FSRS drives the actual schedule.
    """
    __tablename__ = "word_memory_state"

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, unique=True, index=True)

    # FSRS core state
    state = Column(Integer, default=1)             # 1=learning, 2=review, 3=relearning
    step = Column(Integer, default=0)
    stability = Column(Float, nullable=True)       # memory stability in days
    difficulty = Column(Float, nullable=True)      # FSRS difficulty (1-10)
    due = Column(DateTime, nullable=True)          # next review due (naive local)
    last_review = Column(DateTime, nullable=True)  # last review time (naive local)

    # Accumulators
    reps = Column(Integer, default=0)              # total reviews
    lapses = Column(Integer, default=0)            # total "forgot" events

    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

"""Pydantic schemas for structured AI outputs.

These are the contracts the AI Gateway validates against, so a model returning
malformed JSON never reaches the database or the UI as half-formed data.
"""

from pydantic import BaseModel, Field


class ExtractedWord(BaseModel):
    """One candidate vocabulary word recommended by the Material Engine."""
    word: str = Field(min_length=1, max_length=64)
    lemma: str = ""                                    # canonical/lemmatized form
    meaning_zh: str = ""                               # Chinese meaning
    importance: float = Field(default=0.5, ge=0.0, le=1.0)   # 0=skip, 1=must-learn
    difficulty: str = "CET4"                           # 高中 | CET4 | CET6 | 考研 | TOEFL
    reason: str = ""                                   # why worth learning (CN)
    example: str = ""                                  # learner-friendly example (EN)
    source_sentence: str = ""                          # original sentence from material
    tags: list[str] = Field(default_factory=list)      # e.g. ["学术", "高频", "易混"]


class MaterialAnalysis(BaseModel):
    """Full result of analyzing one learning material."""
    document_summary: str = ""
    words: list[ExtractedWord] = Field(default_factory=list)


class ExampleSentence(BaseModel):
    """A cached AI example sentence for one word at one difficulty level."""
    example_en: str = ""
    example_cn: str = ""


class ExerciseQuestion(BaseModel):
    """One AI-generated practice question targeting weak words."""
    type: str = Field(default="multiple_choice")   # multiple_choice|spelling|fill_blank|discrimination
    question: str = ""
    options: list[str] = Field(default_factory=list)
    answer: str = ""
    explanation: str = ""
    difficulty: int = Field(default=2, ge=1, le=5)
    target_words: list[str] = Field(default_factory=list)


class ExerciseSet(BaseModel):
    """A set of practice questions."""
    questions: list[ExerciseQuestion] = Field(default_factory=list)


class ConfusionSet(BaseModel):
    """Two commonly-confused words with a discrimination explanation."""
    words: list[str] = Field(default_factory=list, min_length=2, max_length=2)
    distinction_cn: str = ""
    memory_tip_cn: str = ""
    example_pair: list[ExampleSentence] = Field(default_factory=list)


class LearningAnalysis(BaseModel):
    """AI diagnosis for a single struggling word, based on real review data."""
    diagnosis: str = ""
    mistake_pattern: str = ""
    suggestions: list[str] = Field(default_factory=list)
    practice_sentence: str = ""
    # Richer, machine-usable fields.
    problem_type: str = ""                              # meaning|spelling|confusion|context
    confused_with: list[str] = Field(default_factory=list)
    recommended_exercise_type: str = ""                 # meaning_choice|spelling|context_fill|confusion_choice

"""Pydantic schemas for structured AI outputs.

These are the contracts the AI Gateway validates against, so a model returning
malformed JSON never reaches the database or the UI as half-formed data.
"""

from pydantic import BaseModel, Field


class ExtractedWord(BaseModel):
    """One candidate vocabulary word recommended by the Material Engine."""
    word: str = Field(min_length=1, max_length=64)
    meaning: str = ""
    importance: int = Field(default=3, ge=1, le=5)   # 1=skip, 5=must-learn
    difficulty: int = Field(default=3, ge=1, le=5)   # 1=easy, 5=hard
    reason: str = ""                                  # why worth learning (CN)
    example: str = ""                                 # learner-friendly example (EN)
    source_sentence: str = ""                         # original sentence from material


class MaterialAnalysis(BaseModel):
    """Full result of analyzing one learning material."""
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

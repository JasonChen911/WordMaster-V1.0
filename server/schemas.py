from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WordOut(BaseModel):
    id: int = 0
    english: str
    phonetic: str = ""
    chinese: str = ""
    example_en: str = ""
    example_cn: str = ""
    difficulty: float = 2.5
    is_favorite: bool = False
    is_mastered: bool = False
    review_count: int = 0
    review_stage: int = 0
    accuracy_rate: float = 0.0
    proficiency: int = 0
    study_status: str = "new"
    next_review: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudyRequest(BaseModel):
    word_id: str  # English word text (string-based ID in JSON system)
    result: str  # "too_easy", "know", "fuzzy", "unknown"
    seconds_spent: int = 0  # Time spent on this word in seconds


class StudyResponse(BaseModel):
    message: str
    word: dict


class StatsOut(BaseModel):
    today_studied: int
    total_studied: int
    total_mastered: int
    streak_days: int
    total_words: int
    favorite_count: int
    today_correct: int = 0
    today_total: int = 0
    overall_accuracy: float = 0.0
    proficiency_distribution: dict = {}


class SearchResult(BaseModel):
    words: list[WordOut]
    total: int


class AIExplainRequest(BaseModel):
    english: str
    chinese: str


class AIExplainOut(BaseModel):
    simple_explanation_cn: str = ""
    word_root: str = ""
    memory_tip: str = ""
    example_sentences: list[dict] = []
    ai_available: bool = False


class AIErrorAnalysisOut(BaseModel):
    analysis: str = ""
    weakness_patterns: list[str] = []
    suggestions: list[str] = []
    ai_available: bool = False


class ErrorWordItem(BaseModel):
    english: str
    chinese: str
    wrong_count: int
    accuracy_rate: float


class AIErrorAnalysisRequest(BaseModel):
    error_words: list[ErrorWordItem] = []


class DashboardOut(BaseModel):
    today_words_count: int
    streak_days: int
    total_mastered: int
    total_words: int
    today_studied: int
    progress_percent: float
    recent_records: list[dict] = []
    today_minutes: int = 0
    today_new_words: int = 0
    remaining_words: int = 0
    avg_daily_words: float = 0.0
    est_completion_days: int = 0
    total_minutes: int = 0
    heatmap: list[dict] = []
    active_book: Optional[dict] = None


class WordExplainRequest(BaseModel):
    word: str


class WordExplainResponse(BaseModel):
    word: str
    pos: str = ""            # 词性
    core_meaning: str = ""    # 核心释义
    simple_understanding: str = ""  # 简单理解
    example_en: str = ""      # 英文例句
    example_cn: str = ""      # 中文翻译
    usage_tip: str = ""       # 使用提示
    cached: bool = False      # Whether this came from cache
    ai_available: bool = True
    error: str = ""           # Friendly error message when AI fails

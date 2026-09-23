"""Local Classroom Demo seed data.

This is EXPLICITLY demo data — a clearly-labelled "Demo Class" with fictitious
students and simulated word statistics. It exists only to demonstrate the
teacher dashboard UI. It is never presented as real user data (``is_demo=True``).
"""

DEMO_CLASS_NAME = "Demo Class（演示班级）"

DEMO_COURSE = {
    "name": "大学英语 · 人工智能专题",
    "description": "从《Artificial Intelligence and Education》一文提取的重点词汇（演示课程）。",
}

DEMO_STUDENTS = [
    "张同学", "李同学", "王同学", "赵同学", "陈同学",
    "刘同学", "杨同学", "周同学",
]

# Simulated per-student weak-word records (word, wrong_count, accuracy, lapses).
# The word list mirrors realistic confusable vocabulary (distinguish/distinctive,
# economic/economical, etc.) so the aggregated "class weak points" read plausibly.
DEMO_WEAK_WORDS = [
    ("distinguish", 3, 0.25, 2),
    ("distinctive", 2, 0.33, 1),
    ("economic", 2, 0.40, 1),
    ("economical", 3, 0.20, 2),
    ("affect", 1, 0.50, 1),
    ("approach", 1, 0.60, 0),
    ("significant", 1, 0.50, 1),
    ("evaluate", 2, 0.33, 1),
    ("transform", 1, 0.67, 0),
    ("criteria", 2, 0.40, 1),
]

# Per-student aggregate completion profile (index-matched to DEMO_STUDENTS).
# (words_studied, words_mastered, total_reviews, correct_count, lapses)
DEMO_STUDENT_STATS = [
    (120, 72, 260, 182, 38),
    (98, 51, 220, 143, 35),
    (140, 95, 310, 232, 30),
    (76, 30, 170, 88, 42),
    (110, 68, 250, 175, 33),
    (130, 88, 300, 220, 28),
    (90, 45, 200, 128, 36),
    (105, 60, 240, 165, 31),
]

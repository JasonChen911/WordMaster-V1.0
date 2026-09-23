"""AI services — high-level, product-specific AI capabilities.

Each service returns validated data (via the gateway's ``chat_json``) or a
safe local fallback, so a missing/erroring AI never breaks the feature.
"""

from .material_service import analyze_material, extract_candidates_local, clean_text
from .analysis_service import analyze_word_struggle
from .exercise_service import generate_exercises
from .example_service import get_example

__all__ = [
    "analyze_material",
    "extract_candidates_local",
    "clean_text",
    "analyze_word_struggle",
    "generate_exercises",
    "get_example",
]

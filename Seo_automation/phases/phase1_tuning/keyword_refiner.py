import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phases.phase0_keyword_generation import refine_user_keywords

def refine_keywords(keywords: list, profile: dict) -> dict:
    result = refine_user_keywords(keywords, profile)
    return {
        'final_keywords': result.get('refined_keywords', keywords),
        'removed_keywords': result.get('removed', []),
        'added_keywords': result.get('added', []),
        'notes': result.get('notes', '')
    }

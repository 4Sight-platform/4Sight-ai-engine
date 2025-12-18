import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.onboarding.terminal_ui import *
from shared.profile_manager import get_profile_manager
from phases.phase0_keyword_generation import generate_keywords_for_user, rank_keywords

def run_page(user_id: str) -> dict:
    pm = get_profile_manager()
    print_page_header(6, "Keyword Selection")
    
    profile = pm.load_profile(user_id)
    print_info("Generating keyword suggestions...")
    
    keywords = generate_keywords_for_user(profile, count=30)
    ranked = rank_keywords(keywords, profile)[:15]
    
    pm.save_keywords_generated(user_id, keywords)
    
    print("\nSelect 5-15 keywords:")
    for i, kw in enumerate(ranked, 1):
        print(f"  {i}. {kw['keyword']} (Score: {kw['score']:.1f})")
    
    sel = input("\nEnter numbers (e.g., 1,3,5): ").split(',')
    selected = [ranked[int(i.strip())-1]['keyword'] for i in sel if i.strip().isdigit()]
    
    pm.save_keywords_selected(user_id, selected)
    return {'selected_keywords': selected}

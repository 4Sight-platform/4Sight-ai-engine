import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.onboarding.terminal_ui import *
from shared.profile_manager import get_profile_manager

def run_page(user_id: str) -> dict:
    pm = get_profile_manager()
    print_page_header(5, "SEO Goals")
    
    goals = get_multiple_choice("Select SEO goals", 
        ["Organic traffic growth", "Search visibility", "Local visibility (GMB)", "Top rankings"])
    
    data = {'seo_goals': [["organic_traffic","search_visibility","local_visibility","top_rankings"][i] for i in goals]}
    pm.update_profile(user_id, data)
    return data

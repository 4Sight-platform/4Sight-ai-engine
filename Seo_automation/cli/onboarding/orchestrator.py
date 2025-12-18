import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.profile_manager import get_profile_manager
from cli.onboarding import page1_business, page2_gsc, page3_audience, page4_portfolio, page5_goals, page6_keywords, page7_content, page8_reporting

def run_onboarding() -> str:
    pm = get_profile_manager()
    user_id = pm.create_profile()
    
    pages = [page1_business, page2_gsc, page3_audience, page4_portfolio, page5_goals, page6_keywords, page7_content, page8_reporting]
    
    for page in pages:
        page.run_page(user_id)
    
    print("\n✓ Onboarding complete!")
    return user_id

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.onboarding.terminal_ui import *
from shared.profile_manager import get_profile_manager

def run_page(user_id: str) -> dict:
    pm = get_profile_manager()
    print_page_header(2, "GSC Connection")
    
    print_info("Connect Google Search Console for ranking data")
    gsc_connected = get_yes_no("Have you already connected GSC?", default=False)
    
    data = {'gsc_connected': gsc_connected}
    pm.update_profile(user_id, data)
    return data

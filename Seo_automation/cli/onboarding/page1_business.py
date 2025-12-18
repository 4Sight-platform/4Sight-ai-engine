import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.onboarding.terminal_ui import *
from shared.validators import *
from shared.profile_manager import get_profile_manager

def run_page(user_id: str) -> dict:
    pm = get_profile_manager()
    print_page_header(1, "Business Information")
    
    name = get_input("Business name")
    validate_business_name(name)
    
    url = get_input("Website URL")
    validate_url(url)
    if not url.startswith('http'):
        url = 'https://' + url
    
    desc = get_multiline_input("Business description (max 500 chars)", 500)
    
    data = {'business_name': name, 'website_url': url, 'business_description': desc}
    pm.update_profile(user_id, data)
    return data

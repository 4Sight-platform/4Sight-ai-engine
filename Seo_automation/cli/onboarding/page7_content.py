import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.onboarding.terminal_ui import *
from shared.profile_manager import get_profile_manager

def run_page(user_id: str) -> dict:
    pm = get_profile_manager()
    print_page_header(7, "Content Filter")
    
    home = get_input("Home page URL")
    product = get_input("Product page URL")
    contact = get_input("Contact page URL")
    about = get_input("About page URL")
    blog = get_input("Blog URL")
    
    data = {'page_urls': {'home': home, 'product': product, 'contact': contact, 'about': about, 'blog': blog}}
    pm.update_profile(user_id, data)
    return data

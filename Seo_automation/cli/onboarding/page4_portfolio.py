import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.onboarding.terminal_ui import *
from shared.profile_manager import get_profile_manager

def run_page(user_id: str) -> dict:
    pm = get_profile_manager()
    print_page_header(4, "Business Portfolio")
    
    products = add_items_to_list("Enter your products", max_items=10)
    services = add_items_to_list("Enter your services", max_items=10)
    differentiators = add_items_to_list("What makes you unique?", max_items=5)
    
    data = {'products': products, 'services': services, 'differentiators': differentiators}
    pm.update_profile(user_id, data)
    return data

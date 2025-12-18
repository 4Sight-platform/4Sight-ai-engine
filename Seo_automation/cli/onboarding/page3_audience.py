import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.onboarding.terminal_ui import *
from shared.profile_manager import get_profile_manager

def run_page(user_id: str) -> dict:
    pm = get_profile_manager()
    print_page_header(3, "Audience & Search Intent")
    
    scope = get_choice("Location scope", ["Local", "Regional", "Nationwide", "International"])
    locations = add_items_to_list("Enter locations", max_items=5) if scope in [0,1] else []
    customer = get_input("Describe your target customer")
    intent = get_multiple_choice("Search intent", ["Information", "Comparison", "Deal", "Action-focused"], max_selections=2)
    
    data = {
        'location_scope': ["local","regional","nationwide","international"][scope],
        'selected_locations': locations,
        'customer_description': customer,
        'search_intent': [["information","comparison","deal","action-focused"][i] for i in intent]
    }
    pm.update_profile(user_id, data)
    return data

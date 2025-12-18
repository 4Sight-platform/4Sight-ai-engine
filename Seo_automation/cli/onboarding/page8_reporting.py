import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.onboarding.terminal_ui import *
from shared.profile_manager import get_profile_manager

def run_page(user_id: str) -> dict:
    pm = get_profile_manager()
    print_page_header(8, "Reporting & Notifications")
    
    channels = get_multiple_choice("Reporting channels", ["Email", "Dashboard"])
    emails = add_items_to_list("Email addresses", max_items=5) if 0 in channels else []
    freq = get_choice("Report frequency", ["Daily", "Weekly", "Monthly"])
    
    data = {
        'reporting_channels': [["email","dashboard"][i] for i in channels],
        'email_addresses': emails,
        'report_frequency': ["daily","weekly","monthly"][freq]
    }
    pm.update_profile(user_id, data)
    pm.mark_onboarding_complete(user_id)
    return data

"""
Terminal UI Utilities
Consistent terminal interface for onboarding
"""


class Colors:
    """Terminal color codes"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def clear_screen():
    """Clear terminal screen"""
    import os
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header(text: str):
    """Print page header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.ENDC}\n")


def print_page_header(page_num: int, title: str):
    """Print onboarding page header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  Page {page_num}/8: {title}")
    print(f"{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}→{Colors.ENDC} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠{Colors.ENDC}  {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")


def print_separator():
    """Print separator line"""
    print(f"{Colors.OKBLUE}{'─'*60}{Colors.ENDC}")


def get_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default"""
    if default:
        full_prompt = f"{Colors.OKBLUE}→{Colors.ENDC} {prompt} [{default}]: "
    else:
        full_prompt = f"{Colors.OKBLUE}→{Colors.ENDC} {prompt}: "
    
    value = input(full_prompt).strip()
    
    if not value and default:
        return default
    
    return value


def get_multiline_input(prompt: str, max_chars: int = None) -> str:
    """Get multiline input from user"""
    print(f"{Colors.OKBLUE}→{Colors.ENDC} {prompt}")
    if max_chars:
        print(f"  (Max {max_chars} characters, press Enter twice to finish)")
    else:
        print(f"  (Press Enter twice to finish)")
    
    lines = []
    empty_lines = 0
    
    while True:
        line = input()
        
        if not line:
            empty_lines += 1
            if empty_lines >= 2:
                break
        else:
            empty_lines = 0
            lines.append(line)
    
    text = '\n'.join(lines)
    
    if max_chars and len(text) > max_chars:
        print_warning(f"Text truncated to {max_chars} characters")
        text = text[:max_chars]
    
    return text


def get_choice(prompt: str, choices: list, default: int = None) -> int:
    """Get user choice from list"""
    print(f"\n{Colors.OKBLUE}→{Colors.ENDC} {prompt}\n")
    
    for i, choice in enumerate(choices, 1):
        if default is not None and i - 1 == default:
            print(f"  {i}) {choice} {Colors.OKGREEN}(default){Colors.ENDC}")
        else:
            print(f"  {i}) {choice}")
    
    print()
    
    while True:
        if default is not None:
            choice_input = input(f"Enter choice (1-{len(choices)}) [{default + 1}]: ").strip()
            if not choice_input:
                return default
        else:
            choice_input = input(f"Enter choice (1-{len(choices)}): ").strip()
        
        try:
            choice_num = int(choice_input)
            if 1 <= choice_num <= len(choices):
                return choice_num - 1
            else:
                print_error(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print_error("Please enter a valid number")


def get_multiple_choice(prompt: str, choices: list, max_selections: int = None) -> list:
    """Get multiple selections from user"""
    print(f"\n{Colors.OKBLUE}→{Colors.ENDC} {prompt}")
    if max_selections:
        print(f"  (Select up to {max_selections} options)\n")
    else:
        print(f"  (Select multiple options)\n")
    
    for i, choice in enumerate(choices, 1):
        print(f"  {i}) {choice}")
    
    print()
    print_info("Enter numbers separated by commas (e.g., 1,3,4) or 'all' for all:")
    
    while True:
        selections_input = input(f"{Colors.OKBLUE}→{Colors.ENDC} Your selections: ").strip()
        
        if selections_input.lower() == 'all':
            if max_selections and len(choices) > max_selections:
                print_error(f"Can only select up to {max_selections} options")
                continue
            return list(range(len(choices)))
        
        try:
            selected_nums = [int(x.strip()) for x in selections_input.split(',')]
            
            if not all(1 <= num <= len(choices) for num in selected_nums):
                print_error(f"All numbers must be between 1 and {len(choices)}")
                continue
            
            selected_indices = [num - 1 for num in selected_nums]
            selected_indices = list(set(selected_indices))
            
            if max_selections and len(selected_indices) > max_selections:
                print_error(f"Can only select up to {max_selections} options")
                continue
            
            return selected_indices
        
        except ValueError:
            print_error("Please enter valid numbers separated by commas")


def get_yes_no(prompt: str, default: bool = None) -> bool:
    """Get yes/no answer from user"""
    if default is True:
        suffix = " (Y/n): "
    elif default is False:
        suffix = " (y/N): "
    else:
        suffix = " (y/n): "
    
    while True:
        answer = input(f"{Colors.OKBLUE}→{Colors.ENDC} {prompt}{suffix}").strip().lower()
        
        if not answer and default is not None:
            return default
        
        if answer in ['y', 'yes']:
            return True
        elif answer in ['n', 'no']:
            return False
        else:
            print_error("Please enter 'y' or 'n'")


def show_list_items(items: list, title: str = None):
    """Display list of items"""
    if title:
        print(f"\n{Colors.BOLD}{title}{Colors.ENDC}")
    
    if not items:
        print_info("(none)")
        return
    
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item}")
    
    print()


def add_items_to_list(prompt: str, existing_items: list = None, max_items: int = None) -> list:
    """Allow user to add multiple items to a list"""
    items = existing_items.copy() if existing_items else []
    
    print(f"\n{Colors.OKBLUE}→{Colors.ENDC} {prompt}")
    print(f"  (Enter one item per line, empty line when done)")
    if max_items:
        print(f"  (Maximum {max_items} items)")
    print()
    
    if items:
        show_list_items(items, "Current items:")
    
    while True:
        if max_items and len(items) >= max_items:
            print_warning(f"Maximum {max_items} items reached")
            break
        
        remaining = f" ({max_items - len(items)} remaining)" if max_items else ""
        item = input(f"  Item{remaining}: ").strip()
        
        if not item:
            break
        
        if item in items:
            print_warning("Item already added")
            continue
        
        items.append(item)
        print_success(f"Added: {item}")
    
    return items


def confirm_and_continue() -> bool:
    """Show continue/back/cancel options"""
    print()
    print_separator()
    print(f"\n{Colors.BOLD}Options:{Colors.ENDC}")
    print("  1) Continue to next page")
    print("  2) Go back and edit")
    print("  3) Cancel onboarding")
    
    choice = get_choice("What would you like to do?", 
                       ["Continue", "Go back", "Cancel"], 
                       default=0)
    
    if choice == 0:
        return True
    elif choice == 1:
        return False
    else:
        raise KeyboardInterrupt("Onboarding cancelled by user")


def show_progress(current_page: int, total_pages: int = 8):
    """Show progress bar"""
    filled = int((current_page / total_pages) * 20)
    bar = "█" * filled + "░" * (20 - filled)
    percentage = int((current_page / total_pages) * 100)
    
    print(f"{Colors.OKBLUE}Progress: {bar} {percentage}% ({current_page}/{total_pages}){Colors.ENDC}")
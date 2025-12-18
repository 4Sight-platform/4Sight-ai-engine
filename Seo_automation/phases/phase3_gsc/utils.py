"""
Terminal UI Utilities
Helper functions for pretty terminal output
"""

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_step(step_num, total, message):
    """Print a step indicator"""
    print(f"[{step_num}/{total}] {message}")

def print_success(message):
    """Print a success message"""
    print(f"✓ {message}")

def print_error(message):
    """Print an error message"""
    print(f"✗ {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"⚠️  {message}")

def print_info(message):
    """Print an info message"""
    print(f"→ {message}")

def get_user_input(prompt):
    """Get user input with a prompt"""
    return input(f"→ {prompt}: ").strip()

def get_user_choice(options):
    """
    Display options and get user selection
    
    Args:
        options: List of option strings
        
    Returns:
        int: Selected option index (0-based)
    """
    print("\nSelect an option:")
    for i, option in enumerate(options, 1):
        print(f"  {i}) {option}")
    
    while True:
        try:
            choice = int(input(f"\n→ Enter choice (1-{len(options)}): "))
            if 1 <= choice <= len(options):
                return choice - 1
            else:
                print_error(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print_error("Please enter a valid number")

def confirm_action(message):
    """
    Ask user for yes/no confirmation
    
    Args:
        message: Confirmation prompt
        
    Returns:
        bool: True if user confirms, False otherwise
    """
    response = input(f"→ {message} (y/n): ").strip().lower()
    return response in ['y', 'yes']

def print_table(headers, rows):
    """
    Print a formatted table
    
    Args:
        headers: List of column headers
        rows: List of lists containing row data
    """
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Print header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print("\n" + header_line)
    print("-" * len(header_line))
    
    # Print rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        print(row_line)
    print()
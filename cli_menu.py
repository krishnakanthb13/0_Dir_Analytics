"""
Directory Analytics CLI Tool - CLI Menu Utilities
==================================================
Terminal-based user interface utilities and table display.
"""

import os
import sys


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title, width=60):
    """Print a styled section header."""
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    print()


def print_subheader(title, width=60):
    """Print a styled sub-header."""
    print()
    print("-" * width)
    print(f"  {title}")
    print("-" * width)


def print_table(headers, rows, col_widths=None):
    """
    Print data in a clean ASCII table format.
    
    Args:
        headers: List of column headers
        rows: List of row data (each row is a list/tuple)
        col_widths: Optional list of column widths (auto-calculated if None)
    """
    if not rows:
        print("  (No data to display)")
        return
    
    # Calculate column widths
    if col_widths is None:
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(min(max_width + 2, 50))  # Cap at 50 chars
    
    # Build format string
    format_str = "  " + " | ".join(f"{{:<{w}}}" for w in col_widths)
    separator = "  " + "-+-".join("-" * w for w in col_widths)
    
    # Print table
    print(format_str.format(*[str(h)[:w] for h, w in zip(headers, col_widths)]))
    print(separator)
    for row in rows:
        # Truncate values to fit column width
        formatted_row = []
        for i, (val, width) in enumerate(zip(row, col_widths)):
            str_val = str(val) if val is not None else ""
            if len(str_val) > width:
                str_val = str_val[:width-3] + "..."
            formatted_row.append(str_val)
        print(format_str.format(*formatted_row))
    print()


def print_key_value(key, value, key_width=20):
    """Print a key-value pair with alignment."""
    print(f"  {key:<{key_width}} : {value}")


def get_user_input(prompt, valid_options=None, allow_empty=False):
    """
    Get validated user input.
    
    Args:
        prompt: Input prompt to display
        valid_options: Optional list of valid options
        allow_empty: Whether to allow empty input
    """
    while True:
        try:
            user_input = input(f"\n  {prompt}: ").strip()
            
            if not user_input and allow_empty:
                return ""
            
            if not user_input:
                print("  [!] Please enter a value")
                continue
            
            if valid_options:
                if user_input.lower() in [str(o).lower() for o in valid_options]:
                    return user_input
                else:
                    print(f"  [!] Invalid option. Choose from: {', '.join(map(str, valid_options))}")
                    continue
            
            return user_input
            
        except KeyboardInterrupt:
            print("\n\n  [!] Operation cancelled")
            return None
        except EOFError:
            return None


def get_number_input(prompt, default=None, min_val=1, max_val=1000):
    """Get a numeric input from user."""
    while True:
        default_str = f" [{default}]" if default else ""
        try:
            user_input = input(f"\n  {prompt}{default_str}: ").strip()
            
            if not user_input and default:
                return default
            
            num = int(user_input)
            if min_val <= num <= max_val:
                return num
            else:
                print(f"  [!] Enter a number between {min_val} and {max_val}")
        except ValueError:
            print("  [!] Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\n  [!] Operation cancelled")
            return default


def print_menu(title, options):
    """
    Display a numbered menu.
    
    Args:
        title: Menu title
        options: List of (number, description) tuples
    """
    print_header(title)
    for num, desc in options:
        print(f"    [{num}] {desc}")
    print()


def confirm(prompt):
    """Ask for yes/no confirmation."""
    response = get_user_input(f"{prompt} (y/n)", valid_options=['y', 'n', 'yes', 'no'])
    return response and response.lower() in ['y', 'yes']


def pause():
    """Pause and wait for user to press Enter."""
    try:
        input("\n  Press Enter to continue...")
    except (KeyboardInterrupt, EOFError):
        pass


def print_banner():
    """Print the application banner."""
    clear_screen()
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║         DIRECTORY ANALYTICS CLI TOOL                     ║
    ║         ─────────────────────────────                    ║
    ║         Scan • Analyze • Discover                        ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

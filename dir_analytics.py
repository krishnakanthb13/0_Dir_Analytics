"""
Directory Analytics CLI Tool - Main Entry Point
================================================
Production-ready CLI tool for directory scanning and analytics.

Usage: Run Dir_Analytics.bat or execute directly with Python.
"""

import sys
import os

# Add script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    get_scan_directory, set_scan_directory, get_all_directories, get_current_index,
    DATABASE_PATH, DATA_FOLDER, MAX_SAME_SIZE_FILES, SQL_FILE_PATH, DB_BROWSER_PATH
)
from database import init_db, export_to_csv, get_file_count, vacuum_database
from scanner import scan_directory
from analytics import (
    get_top_n_files, get_smallest_files, get_statistics, get_type_statistics,
    find_duplicates, get_duplicate_stats, get_space_hogs, get_extension_dominance,
    get_age_analysis, get_zero_byte_files, get_deleted_files,
    run_duplicate_detection, get_potential_duplicate_count
)
from cli_menu import (
    clear_screen, print_header, print_subheader, print_table, print_key_value,
    get_user_input, get_number_input, print_menu, pause, print_banner, confirm
)
from logger import start_logging, stop_logging, get_log_file


def show_main_menu():
    """Display and handle main menu."""
    while True:
        print_banner()
        
        # Show current configuration
        current_dir = get_scan_directory()
        print(f"    Scan Directory : {current_dir}")
        file_count = get_file_count() if os.path.exists(DATABASE_PATH) else 0
        print(f"    Files in DB    : {file_count:,}")
        print()
        
        print_menu("MAIN MENU", [
            ("1", "Scan Directory"),
            ("2", "View Analytics"),
            ("3", "Export to CSV"),
            ("4", "Switch Directory"),
            ("5", "Open in DB Browser"),
            ("6", "Compact Database"),
            ("7", "Exit")
        ])
        
        choice = get_user_input("Select option", valid_options=['1', '2', '3', '4', '5', '6', '7'])
        
        if choice == '1':
            run_scan()
        elif choice == '2':
            show_analytics_menu()
        elif choice == '3':
            run_export()
        elif choice == '4':
            switch_directory()
        elif choice == '5':
            open_db_browser()
        elif choice == '6':
            run_vacuum()
        elif choice == '7' or choice is None:
            print("\n  Goodbye!\n")
            sys.exit(0)


def run_scan():
    """Execute directory scan."""
    clear_screen()
    print_header("DIRECTORY SCAN")
    current_dir = get_scan_directory()
    print(f"  Target: {current_dir}")
    print()
    
    if not os.path.exists(current_dir):
        print(f"  [ERROR] Directory not found: {current_dir}")
        print("  Please update SCAN_DIRECTORIES in config.py")
        pause()
        return
    
    if confirm("Start scanning?"):
        scan_directory()
    else:
        print("  Scan cancelled.")
    
    pause()


def switch_directory():
    """Switch between configured directories."""
    clear_screen()
    print_header("SWITCH DIRECTORY")
    
    directories = get_all_directories()
    current_idx = get_current_index()
    
    print("  Available directories:\n")
    for idx, dir_path in directories:
        marker = " → " if idx == current_idx else "   "
        print(f"    [{idx + 1}]{marker}{dir_path}")
    
    print(f"\n    [0]    Back to Main Menu")
    print()
    
    valid_options = ['0'] + [str(i + 1) for i in range(len(directories))]
    choice = get_user_input("Select directory", valid_options=valid_options)
    
    if choice == '0' or choice is None:
        return
    
    new_idx = int(choice) - 1
    if set_scan_directory(new_idx):
        new_dir = get_scan_directory()
        print(f"\n  [OK] Switched to: {new_dir}")
        
        # Show file count for new directory
        file_count = get_file_count()
        print(f"       Files in DB for this directory: {file_count:,}")
    else:
        print("\n  [ERROR] Invalid selection")
    
    pause()


def run_export():
    """Export database to CSV."""
    clear_screen()
    print_header("EXPORT TO CSV")
    
    if not os.path.exists(DATABASE_PATH):
        print("  [ERROR] No database found. Run a scan first.")
        pause()
        return
    
    if confirm("Export all data to CSV?"):
        print("\n  Exporting...")
        filepath, count = export_to_csv()
        print(f"\n  [OK] Exported {count} records to:")
        print(f"       {filepath}")
    
    pause()


def open_db_browser():
    """Open database and SQL file in DB Browser for SQLite."""
    import subprocess
    
    clear_screen()
    print_header("OPEN IN DB BROWSER")
    
    # Check if DB Browser exists
    if not os.path.exists(DB_BROWSER_PATH):
        print(f"  [ERROR] DB Browser not found at:")
        print(f"          {DB_BROWSER_PATH}")
        print()
        print("  Please update DB_BROWSER_PATH in config.py")
        pause()
        return
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print("  [ERROR] No database found. Run a scan first.")
        pause()
        return
    
    print(f"  Database: {DATABASE_PATH}")
    print(f"  SQL File: {SQL_FILE_PATH}")
    print()
    
    print_menu("OPEN OPTIONS", [
        ("1", "Open Database (.db)"),
        ("2", "Open SQL Queries (.sql)"),
        ("3", "Open Database + SQL Instructions"),
        ("0", "Back to Main Menu")
    ])
    
    choice = get_user_input("Select option", valid_options=['0', '1', '2', '3'])
    
    if choice == '0' or choice is None:
        return
    
    try:
        if choice == '1':
            print("\n  Opening database in DB Browser...")
            subprocess.Popen([DB_BROWSER_PATH, DATABASE_PATH])
            print("  [OK] Database opened!")
        elif choice == '2':
            print("\n  Opening SQL file in DB Browser...")
            subprocess.Popen([DB_BROWSER_PATH, SQL_FILE_PATH])
            print("  [OK] SQL file opened!")
        elif choice == '3':
            print("\n  Opening database in DB Browser...")
            subprocess.Popen([DB_BROWSER_PATH, DATABASE_PATH])
            print("  [OK] Database opened!")
            print()
            print("  To load SQL queries in DB Browser:")
            print("    1. Go to 'Execute SQL' tab")
            print("    2. Click 'Open SQL file' button (folder icon)")
            print("    3. Navigate to:")
            print(f"       {SQL_FILE_PATH}")
            print("    4. Select query and press F5 or click 'Execute'")
            print()
            print("  TIP: Each query is separated by comments.")
    except Exception as e:
        print(f"\n  [ERROR] Failed to open: {e}")
    
    pause()


def run_vacuum():
    """Compact the database to reclaim space."""
    clear_screen()
    print_header("COMPACT DATABASE")
    
    if not os.path.exists(DATABASE_PATH):
        print("  [ERROR] No database found. Run a scan first.")
        pause()
        return
    
    # Show current size
    from scanner import format_size
    current_size = os.path.getsize(DATABASE_PATH)
    print(f"  Current DB Size: {format_size(current_size)}")
    print()
    print("  VACUUM will:")
    print("    - Remove unused space from deleted records")
    print("    - Defragment the database file")
    print("    - Rebuild indexes for better performance")
    print()
    
    if confirm("Compact database now?"):
        print("\n  Compacting...")
        size_before, size_after, saved = vacuum_database()
        
        print(f"\n  [OK] Database compacted!")
        print(f"       Before: {format_size(size_before)}")
        print(f"       After:  {format_size(size_after)}")
        if saved > 0:
            print(f"       Saved:  {format_size(saved)} ({saved * 100 // size_before}%)")
        else:
            print(f"       (No space to reclaim - database is already optimized)")
    
    pause()


def show_analytics_menu():
    """Display and handle analytics submenu."""
    if not os.path.exists(DATABASE_PATH):
        clear_screen()
        print_header("ANALYTICS")
        print("  [ERROR] No database found. Run a scan first.")
        pause()
        return
    
    while True:
        clear_screen()
        print_menu("ANALYTICS MENU", [
            ("1", "Top N Largest Files"),
            ("2", "Overall Statistics"),
            ("3", "File Type Analysis"),
            ("4", "Duplicate Files"),
            ("5", "Space Hog Directories"),
            ("6", "File Age Analysis"),
            ("7", "Zero-Byte Files"),
            ("8", "Deleted Files (Soft)"),
            ("9", "Extension Dominance"),
            ("0", "Back to Main Menu")
        ])
        
        choice = get_user_input("Select option", 
                                valid_options=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
        
        if choice == '0' or choice is None:
            return
        elif choice == '1':
            view_top_files()
        elif choice == '2':
            view_statistics()
        elif choice == '3':
            view_type_analysis()
        elif choice == '4':
            view_duplicates()
        elif choice == '5':
            view_space_hogs()
        elif choice == '6':
            view_age_analysis()
        elif choice == '7':
            view_zero_byte_files()
        elif choice == '8':
            view_deleted_files()
        elif choice == '9':
            view_extension_dominance()


def view_top_files():
    """View top N largest files."""
    clear_screen()
    print_header("TOP LARGEST FILES")
    
    n = get_number_input("How many files to show?", default=10, min_val=1, max_val=100)
    files = get_top_n_files(n)
    
    headers = ["#", "File Name", "Size", "Extension", "Path"]
    rows = []
    for i, f in enumerate(files, 1):
        # Truncate path for display
        path = f['full_path']
        if len(path) > 40:
            path = "..." + path[-37:]
        rows.append([i, f['file_name'], f['file_size_readable'], f['file_extension'], path])
    
    print_table(headers, rows, col_widths=[4, 25, 12, 10, 40])
    pause()


def view_statistics():
    """View overall statistics."""
    clear_screen()
    print_header("OVERALL STATISTICS")
    
    stats = get_statistics()
    
    print_subheader("File Overview")
    print_key_value("Total Active Files", f"{stats['total_files']:,}")
    print_key_value("Total Size", stats['total_size_readable'])
    print_key_value("Unique Directories", f"{stats['total_directories']:,}")
    print_key_value("Unique Extensions", f"{stats['unique_extensions']:,}")
    
    print_subheader("Size Extremes")
    print_key_value("Largest File", f"{stats['largest_file'][0]} ({stats['largest_file'][1]})")
    print_key_value("Smallest File", f"{stats['smallest_file'][0]} ({stats['smallest_file'][1]})")
    
    print_subheader("Deleted Files (Tracked)")
    print_key_value("Deleted Count", f"{stats['deleted_files']:,}")
    print_key_value("Deleted Size", stats['deleted_size_readable'])
    
    # Duplicate stats
    dup_stats = get_duplicate_stats()
    print_subheader("Duplicate Files")
    print_key_value("Duplicate Files", f"{dup_stats['duplicate_files']:,}")
    print_key_value("Potential Waste", dup_stats['wasted_space'])
    
    pause()


def view_type_analysis():
    """View file type breakdown."""
    clear_screen()
    print_header("FILE TYPE ANALYSIS")
    
    stats = get_type_statistics()
    
    headers = ["Extension", "Count", "Total Size", "% of Total"]
    rows = [[s['extension'], s['count'], s['size_readable'], s['percentage']] for s in stats[:20]]
    
    print_table(headers, rows, col_widths=[15, 10, 15, 12])
    
    if len(stats) > 20:
        print(f"  ... and {len(stats) - 20} more extensions")
    
    pause()


def view_duplicates():
    """View duplicate files with lazy hashing."""
    clear_screen()
    print_header("DUPLICATE FILES (LAZY HASHING)")
    
    # Check existing duplicates
    duplicates = find_duplicates()
    dup_stats = get_duplicate_stats()
    
    # Show current state
    total_candidates, size_groups = get_potential_duplicate_count()
    
    print_subheader("Current Status")
    print_key_value("Duplicate Groups Found", f"{dup_stats['duplicate_groups']:,}")
    print_key_value("Duplicate Files", f"{dup_stats['duplicate_files']:,}")
    print_key_value("Wasted Space", dup_stats['wasted_space'])
    print()
    print_key_value("Unhashed Candidates", f"{total_candidates:,} files in {size_groups} size groups")
    print(f"  (Files sharing same size, limit: {MAX_SAME_SIZE_FILES} per group)")
    
    if total_candidates > 0:
        print()
        if confirm("Run duplicate detection now? (will hash candidate files)"):
            print("\n  Computing hashes for candidate files...")
            
            def progress(current, total):
                pct = (current / total * 100) if total > 0 else 0
                print(f"    Progress: {current}/{total} ({pct:.0f}%)", end='\r')
            
            files_hashed, groups_found, stats = run_duplicate_detection(progress)
            print(f"    Progress: Complete!                    ")
            print(f"\n  [OK] Hashed {files_hashed} files, found {groups_found} duplicate groups")
            print(f"       Wasted space: {stats['wasted_bytes'] / (1024*1024):.2f} MB")
            
            # Refresh duplicates after detection
            duplicates = find_duplicates()
            dup_stats = get_duplicate_stats()
    
    if not duplicates:
        print("\n  No duplicate files detected.")
        pause()
        return
    
    print()
    print_subheader(f"Duplicate Groups ({len(duplicates)} total)")
    
    # Show first 5 duplicate groups
    for i, group in enumerate(duplicates[:5], 1):
        print(f"\n  Group {group['group_id']} - {group['count']} files, {group['size']} each")
        print(f"  Hash: {group['hash']}")
        for f in group['files']:
            path = f['full_path']
            if len(path) > 60:
                path = "..." + path[-57:]
            print(f"    - {path}")
    
    if len(duplicates) > 5:
        print(f"\n  ... and {len(duplicates) - 5} more duplicate groups")
    
    pause()


def view_space_hogs():
    """View directories consuming most space."""
    clear_screen()
    print_header("SPACE HOG DIRECTORIES")
    
    n = get_number_input("How many directories?", default=10, min_val=1, max_val=50)
    hogs = get_space_hogs(n)
    
    headers = ["#", "Directory", "Files", "Size"]
    rows = []
    for i, h in enumerate(hogs, 1):
        # Truncate directory path
        directory = h['directory']
        if len(directory) > 50:
            directory = "..." + directory[-47:]
        rows.append([i, directory, h['file_count'], h['size_readable']])
    
    print_table(headers, rows, col_widths=[4, 50, 8, 12])
    pause()


def view_age_analysis():
    """View file age analysis."""
    clear_screen()
    print_header("FILE AGE ANALYSIS")
    
    age_data = get_age_analysis()
    
    print_subheader("5 Oldest Files")
    headers = ["File Name", "Modified", "Size"]
    rows = [[f['file_name'], f['modified_timestamp'][:10] if f['modified_timestamp'] else 'N/A', 
             f['file_size_readable']] for f in age_data['oldest']]
    print_table(headers, rows, col_widths=[30, 12, 12])
    
    print_subheader("5 Newest Files")
    rows = [[f['file_name'], f['modified_timestamp'][:10] if f['modified_timestamp'] else 'N/A',
             f['file_size_readable']] for f in age_data['newest']]
    print_table(headers, rows, col_widths=[30, 12, 12])
    
    pause()


def view_zero_byte_files():
    """View zero-byte (empty) files."""
    clear_screen()
    print_header("ZERO-BYTE FILES")
    
    files = get_zero_byte_files()
    
    if not files:
        print("  No zero-byte files found.")
        pause()
        return
    
    print(f"  Found {len(files)} empty files:\n")
    
    headers = ["File Name", "Path"]
    rows = []
    for f in files[:30]:
        path = f['full_path']
        if len(path) > 50:
            path = "..." + path[-47:]
        rows.append([f['file_name'], path])
    
    print_table(headers, rows, col_widths=[30, 50])
    
    if len(files) > 30:
        print(f"  ... and {len(files) - 30} more empty files")
    
    pause()


def view_deleted_files():
    """View soft-deleted files."""
    clear_screen()
    print_header("DELETED FILES (TRACKED)")
    
    files = get_deleted_files()
    
    if not files:
        print("  No deleted files tracked.")
        print("  (Files are marked deleted when they disappear from disk after a rescan)")
        pause()
        return
    
    print(f"  Found {len(files)} deleted files:\n")
    
    headers = ["File Name", "Size", "Deleted At"]
    rows = [[f['file_name'], f['file_size_readable'], 
             f['deleted_at'][:19] if f['deleted_at'] else 'N/A'] for f in files[:30]]
    
    print_table(headers, rows, col_widths=[30, 12, 20])
    
    if len(files) > 30:
        print(f"  ... and {len(files) - 30} more deleted files")
    
    pause()


def view_extension_dominance():
    """View extension dominance ranking."""
    clear_screen()
    print_header("EXTENSION DOMINANCE RANKING")
    
    data = get_extension_dominance()
    
    headers = ["Rank", "Extension", "Count", "Count %", "Size", "Size %", "Avg Size"]
    rows = []
    for i, d in enumerate(data[:20], 1):
        rows.append([
            i, d['extension'], d['count'], d['count_pct'],
            d['size_readable'], d['percentage'], d['avg_size']
        ])
    
    print_table(headers, rows, col_widths=[5, 15, 8, 10, 12, 10, 12])
    
    if len(data) > 20:
        print(f"  ... and {len(data) - 20} more extensions")
    
    pause()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        # Ensure data folder exists
        os.makedirs(DATA_FOLDER, exist_ok=True)
        
        # Start logging
        log_file = start_logging()
        print(f"  Logging to: {log_file}")
        
        # Run main menu
        show_main_menu()
        
    except KeyboardInterrupt:
        print("\n\n  [!] Interrupted. Goodbye!\n")
        stop_logging()
        sys.exit(0)
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        print("  Please check your configuration and try again.")
        stop_logging()
        sys.exit(1)
    finally:
        stop_logging()

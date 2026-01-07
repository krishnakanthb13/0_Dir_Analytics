"""
Directory Analytics CLI Tool - Configuration
=============================================
Centralized configuration for scan directory, database paths, and settings.
"""

import os

# =============================================================================
# SCAN DIRECTORIES - ADD YOUR DIRECTORIES HERE
# =============================================================================
SCAN_DIRECTORIES = [
    r"D:\\",
    r"E:\\",
    r"C:\Users\ADMIN\Downloads",
    r"C:\Users\ADMIN\Documents",
    r"C:\Users\ADMIN\OneDrive\Documents",
    r"C:\Users\ADMIN\OneDrive\Desktop",
    r"C:\Users\ADMIN\OneDrive\Pictures",
]

# Current selection index (0 = first directory)
_current_directory_index = 0

def get_scan_directory():
    """Get the currently selected scan directory."""
    return SCAN_DIRECTORIES[_current_directory_index]

def set_scan_directory(index):
    """Set the current scan directory by index."""
    global _current_directory_index
    if 0 <= index < len(SCAN_DIRECTORIES):
        _current_directory_index = index
        return True
    return False

def get_all_directories():
    """Get list of all configured directories with their index."""
    return list(enumerate(SCAN_DIRECTORIES))

def get_current_index():
    """Get the current directory index."""
    return _current_directory_index

# For backward compatibility
SCAN_DIRECTORY = SCAN_DIRECTORIES[0]

# =============================================================================
# DATA FILE PATHS (Auto-configured relative to script location)
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(SCRIPT_DIR, "Data File")
DATABASE_PATH = os.path.join(DATA_FOLDER, "dir_analytics.db")
SQL_FILE_PATH = os.path.join(SCRIPT_DIR, "dir_analytics.sql")

# DB Browser for SQLite path (update if installed elsewhere)
DB_BROWSER_PATH = r"C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe"

# =============================================================================
# SCANNING SETTINGS
# =============================================================================
HASH_ALGORITHM = "md5"           # Options: md5, sha1, sha256
HASH_CHUNK_SIZE = 8192           # Bytes to read per chunk when hashing
PROGRESS_INTERVAL = 100          # Print progress every N files
SKIP_HIDDEN_FILES = False        # Skip files starting with '.'
MAX_PATH_LENGTH = 260            # Windows default, extended paths handled

# =============================================================================
# LAZY HASHING SETTINGS (for duplicate detection)
# =============================================================================
MAX_SAME_SIZE_FILES = 100        # Skip hashing if >N files share same size
MIN_FILE_SIZE_FOR_HASH = 1       # Skip hashing empty/tiny files (bytes)

# =============================================================================
# ANALYTICS DEFAULTS
# =============================================================================
DEFAULT_TOP_N = 10               # Default number for "Top N" queries

# =============================================================================
# CSV COLUMN HEADERS (Schema definition)
# =============================================================================
CSV_COLUMNS = [
    "id",
    "file_name",
    "file_extension",
    "file_size_bytes",
    "file_size_readable",
    "parent_directory",
    "full_path",
    "scan_root_directory",
    "created_timestamp",
    "modified_timestamp",
    "file_hash",
    "duplicate_group",
    "hash_computed_at",
    "is_deleted",
    "first_seen",
    "last_seen",
    "deleted_at"
]

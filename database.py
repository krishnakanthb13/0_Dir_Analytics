"""
Directory Analytics CLI Tool - Database Module
===============================================
SQLite database operations for file metadata storage with soft delete support.
Supports lazy hashing for fast scanning with on-demand duplicate detection.
Supports multi-directory tracking with filtering by current scan directory.
"""

import os
import sqlite3
import csv
import hashlib
from datetime import datetime
from config import (
    DATA_FOLDER, DATABASE_PATH, CSV_COLUMNS, get_scan_directory,
    HASH_ALGORITHM, HASH_CHUNK_SIZE, MAX_SAME_SIZE_FILES, MIN_FILE_SIZE_FOR_HASH
)


def get_connection():
    """Get SQLite database connection."""
    os.makedirs(DATA_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like row access
    return conn


def normalize_path(path):
    """Normalize path for consistent storage and comparison."""
    return os.path.normpath(path).rstrip(os.sep)


def get_current_scan_root():
    """Get the normalized current scan directory."""
    return normalize_path(get_scan_directory())


def init_db():
    """Initialize database with schema and indexes."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create files table with soft delete, lazy hashing, and multi-directory support
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_extension TEXT,
            file_size_bytes INTEGER,
            file_size_readable TEXT,
            parent_directory TEXT,
            full_path TEXT UNIQUE,
            scan_root_directory TEXT,
            created_timestamp TEXT,
            modified_timestamp TEXT,
            file_hash TEXT,
            duplicate_group INTEGER,
            hash_computed_at TEXT,
            is_deleted INTEGER DEFAULT 0,
            first_seen TEXT,
            last_seen TEXT,
            deleted_at TEXT
        )
    """)
    
    # Add new columns if they don't exist (for existing databases)
    new_columns = [
        ("duplicate_group", "INTEGER"),
        ("hash_computed_at", "TEXT"),
        ("scan_root_directory", "TEXT")
    ]
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    # Create indexes for fast queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash ON files(file_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deleted ON files(is_deleted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extension ON files(file_extension)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_full_path ON files(full_path)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_size ON files(file_size_bytes)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dup_group ON files(duplicate_group)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_root ON files(scan_root_directory)")
    
    conn.commit()
    conn.close()
    print(f"  [OK] Database initialized: {DATABASE_PATH}")


def upsert_file(metadata, scan_root=None):
    """
    Insert new file or update existing file by full_path.
    Returns: 'inserted', 'updated', or 'restored'
    """
    if scan_root is None:
        scan_root = get_current_scan_root()
    
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # Check if file exists
    cursor.execute("SELECT id, is_deleted FROM files WHERE full_path = ?", 
                   (metadata['full_path'],))
    existing = cursor.fetchone()
    
    if existing is None:
        # New file - INSERT
        cursor.execute("""
            INSERT INTO files (
                file_name, file_extension, file_size_bytes, file_size_readable,
                parent_directory, full_path, scan_root_directory,
                created_timestamp, modified_timestamp,
                file_hash, is_deleted, first_seen, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (
            metadata['file_name'],
            metadata['file_extension'],
            metadata['file_size_bytes'],
            metadata['file_size_readable'],
            metadata['parent_directory'],
            metadata['full_path'],
            scan_root,
            metadata['created_timestamp'],
            metadata['modified_timestamp'],
            metadata['file_hash'],
            now, now
        ))
        result = 'inserted'
    else:
        # Existing file - UPDATE (don't overwrite hash if already computed)
        was_deleted = existing['is_deleted'] == 1
        cursor.execute("""
            UPDATE files SET
                file_name = ?,
                file_extension = ?,
                file_size_bytes = ?,
                file_size_readable = ?,
                parent_directory = ?,
                scan_root_directory = ?,
                created_timestamp = ?,
                modified_timestamp = ?,
                is_deleted = 0,
                last_seen = ?,
                deleted_at = NULL
            WHERE full_path = ?
        """, (
            metadata['file_name'],
            metadata['file_extension'],
            metadata['file_size_bytes'],
            metadata['file_size_readable'],
            metadata['parent_directory'],
            scan_root,
            metadata['created_timestamp'],
            metadata['modified_timestamp'],
            now,
            metadata['full_path']
        ))
        result = 'restored' if was_deleted else 'updated'
    
    conn.commit()
    conn.close()
    return result


def mark_deleted(paths_to_delete):
    """Mark files as deleted (soft delete) for paths no longer on disk."""
    if not paths_to_delete:
        return 0
    
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # Mark each path as deleted
    count = 0
    for path in paths_to_delete:
        cursor.execute("""
            UPDATE files SET is_deleted = 1, deleted_at = ?
            WHERE full_path = ? AND is_deleted = 0
        """, (now, path))
        count += cursor.rowcount
    
    conn.commit()
    conn.close()
    return count


def get_all_active_paths(scan_root=None):
    """Get all file paths currently marked as active (not deleted) for current scan root."""
    if scan_root is None:
        scan_root = get_current_scan_root()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_path FROM files 
        WHERE is_deleted = 0 AND scan_root_directory = ?
    """, (scan_root,))
    paths = {row['full_path'] for row in cursor.fetchall()}
    conn.close()
    return paths


def get_file_count(scan_root=None):
    """Get count of active (non-deleted) files for current scan root."""
    if scan_root is None:
        scan_root = get_current_scan_root()
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM files 
            WHERE is_deleted = 0 AND scan_root_directory = ?
        """, (scan_root,))
        count = cursor.fetchone()['count']
        conn.close()
        return count
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return 0


def get_all_scan_roots():
    """Get list of all unique scan root directories in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT scan_root_directory, COUNT(*) as file_count
        FROM files
        WHERE scan_root_directory IS NOT NULL
        GROUP BY scan_root_directory
        ORDER BY file_count DESC
    """)
    roots = [(row['scan_root_directory'], row['file_count']) for row in cursor.fetchall()]
    conn.close()
    return roots


# =============================================================================
# LAZY HASHING FUNCTIONS
# =============================================================================

def calculate_hash(filepath):
    """Calculate file hash (MD5 by default) for duplicate detection."""
    try:
        hash_func = hashlib.new(HASH_ALGORITHM)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except (PermissionError, OSError, FileNotFoundError):
        return None


def get_size_candidates(scan_root=None):
    """
    Find files that share the same size (potential duplicates) for current scan root.
    Returns dict: {size_bytes: [(id, full_path, file_hash), ...]}
    """
    if scan_root is None:
        scan_root = get_current_scan_root()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Find sizes that have multiple files (candidates for duplicates)
    cursor.execute("""
        SELECT file_size_bytes, COUNT(*) as cnt
        FROM files
        WHERE is_deleted = 0 AND file_size_bytes >= ? AND scan_root_directory = ?
        GROUP BY file_size_bytes
        HAVING COUNT(*) > 1 AND COUNT(*) <= ?
        ORDER BY file_size_bytes DESC
    """, (MIN_FILE_SIZE_FOR_HASH, scan_root, MAX_SAME_SIZE_FILES))
    
    size_groups = cursor.fetchall()
    
    candidates = {}
    for row in size_groups:
        size = row['file_size_bytes']
        cursor.execute("""
            SELECT id, full_path, file_hash
            FROM files
            WHERE is_deleted = 0 AND file_size_bytes = ? AND scan_root_directory = ?
        """, (size, scan_root))
        candidates[size] = [(r['id'], r['full_path'], r['file_hash']) for r in cursor.fetchall()]
    
    conn.close()
    return candidates


def compute_hashes_for_candidates(progress_callback=None, scan_root=None):
    """
    Compute hashes for files that are potential duplicates (same size).
    Only hashes files that don't already have a hash.
    Returns: (files_hashed, duplicate_groups_found)
    """
    if scan_root is None:
        scan_root = get_current_scan_root()
    
    candidates = get_size_candidates(scan_root)
    
    if not candidates:
        return 0, 0
    
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    files_hashed = 0
    total_candidates = sum(len(files) for files in candidates.values())
    processed = 0
    
    # Hash each candidate file that doesn't have a hash yet
    for size, files in candidates.items():
        for file_id, filepath, existing_hash in files:
            processed += 1
            
            if progress_callback and processed % 10 == 0:
                progress_callback(processed, total_candidates)
            
            if existing_hash is not None:
                continue  # Already hashed
            
            # Check if file still exists
            if not os.path.exists(filepath):
                continue
            
            # Compute hash
            file_hash = calculate_hash(filepath)
            if file_hash:
                cursor.execute("""
                    UPDATE files SET file_hash = ?, hash_computed_at = ?
                    WHERE id = ?
                """, (file_hash, now, file_id))
                files_hashed += 1
    
    conn.commit()
    
    # Now assign duplicate groups
    duplicate_groups = assign_duplicate_groups(cursor, scan_root)
    
    conn.commit()
    conn.close()
    
    return files_hashed, duplicate_groups


def assign_duplicate_groups(cursor=None, scan_root=None):
    """
    Assign duplicate_group IDs to files with matching hashes.
    Returns number of duplicate groups found.
    """
    if scan_root is None:
        scan_root = get_current_scan_root()
    
    close_conn = False
    if cursor is None:
        conn = get_connection()
        cursor = conn.cursor()
        close_conn = True
    
    # Reset all duplicate groups for this scan root
    cursor.execute("""
        UPDATE files SET duplicate_group = NULL 
        WHERE scan_root_directory = ?
    """, (scan_root,))
    
    # Find hashes that appear more than once
    cursor.execute("""
        SELECT file_hash, COUNT(*) as cnt
        FROM files
        WHERE is_deleted = 0 AND file_hash IS NOT NULL AND scan_root_directory = ?
        GROUP BY file_hash
        HAVING COUNT(*) > 1
    """, (scan_root,))
    
    duplicate_hashes = cursor.fetchall()
    
    # Assign group numbers
    for group_id, row in enumerate(duplicate_hashes, 1):
        file_hash = row['file_hash']
        cursor.execute("""
            UPDATE files SET duplicate_group = ?
            WHERE file_hash = ? AND is_deleted = 0 AND scan_root_directory = ?
        """, (group_id, file_hash, scan_root))
    
    if close_conn:
        cursor.connection.commit()
        cursor.connection.close()
    
    return len(duplicate_hashes)


def get_duplicate_group_stats(scan_root=None):
    """Get statistics about duplicate groups for current scan root."""
    if scan_root is None:
        scan_root = get_current_scan_root()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Count files with duplicates
    cursor.execute("""
        SELECT COUNT(*) as total_dup_files,
               COUNT(DISTINCT duplicate_group) as num_groups
        FROM files
        WHERE is_deleted = 0 AND duplicate_group IS NOT NULL AND scan_root_directory = ?
    """, (scan_root,))
    result = cursor.fetchone()
    
    # Calculate wasted space (all but one copy per group)
    cursor.execute("""
        SELECT SUM(wasted) as total_wasted FROM (
            SELECT (COUNT(*) - 1) * file_size_bytes as wasted
            FROM files
            WHERE is_deleted = 0 AND duplicate_group IS NOT NULL AND scan_root_directory = ?
            GROUP BY duplicate_group
        )
    """, (scan_root,))
    wasted = cursor.fetchone()['total_wasted'] or 0
    
    conn.close()
    
    return {
        'duplicate_files': result['total_dup_files'] or 0,
        'duplicate_groups': result['num_groups'] or 0,
        'wasted_bytes': wasted
    }


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_to_csv(output_path=None, scan_root=None):
    """Export file data for current scan root to CSV backup."""
    if scan_root is None:
        scan_root = get_current_scan_root()
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(DATA_FOLDER, f"export_{timestamp}.csv")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM files 
        WHERE scan_root_directory = ?
        ORDER BY full_path
    """, (scan_root,))
    rows = cursor.fetchall()
    conn.close()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            row_data = []
            for col in CSV_COLUMNS:
                try:
                    row_data.append(row[col])
                except (IndexError, KeyError):
                    row_data.append(None)
            writer.writerow(row_data)
    
    return output_path, len(rows)


def execute_query(query, params=None):
    """Execute a custom SQL query and return results."""
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def vacuum_database():
    """
    Compact the database by running VACUUM.
    Reclaims unused space and defragments the database file.
    Returns: (size_before, size_after, saved_bytes)
    """
    if not os.path.exists(DATABASE_PATH):
        return 0, 0, 0
    
    # Get size before
    size_before = os.path.getsize(DATABASE_PATH)
    
    # Run VACUUM
    conn = get_connection()
    conn.execute("VACUUM")
    conn.close()
    
    # Get size after
    size_after = os.path.getsize(DATABASE_PATH)
    saved = size_before - size_after
    
    return size_before, size_after, saved

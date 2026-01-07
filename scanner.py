"""
Directory Analytics CLI Tool - Scanner Module
==============================================
Recursive directory scanning with metadata extraction.
Uses in-memory collection with bulk insert for maximum speed.
"""

import os
import hashlib
from datetime import datetime
from config import (
    get_scan_directory, HASH_ALGORITHM, HASH_CHUNK_SIZE, 
    PROGRESS_INTERVAL, SKIP_HIDDEN_FILES
)
from database import init_db, normalize_path, get_connection


def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


def calculate_hash(filepath):
    """Calculate file hash (MD5 by default) for duplicate detection."""
    try:
        hash_func = hashlib.new(HASH_ALGORITHM)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except (PermissionError, OSError):
        return None


def get_file_metadata(filepath):
    """Extract all metadata for a single file."""
    try:
        stat_info = os.stat(filepath)
        
        # Get timestamps
        try:
            created = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
        except (OSError, ValueError):
            created = None
            
        try:
            modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        except (OSError, ValueError):
            modified = None
        
        file_name = os.path.basename(filepath)
        _, ext = os.path.splitext(file_name)
        ext = ext.lower() if ext else "(no extension)"
        
        return {
            'file_name': file_name,
            'file_extension': ext,
            'file_size_bytes': stat_info.st_size,
            'file_size_readable': format_size(stat_info.st_size),
            'parent_directory': os.path.dirname(filepath),
            'full_path': filepath,
            'created_timestamp': created,
            'modified_timestamp': modified,
            'file_hash': None  # Lazy hashing - computed on-demand
        }
    except (PermissionError, OSError, FileNotFoundError):
        return None


def scan_directory(directory=None):
    """
    Recursively scan directory and sync with database.
    Uses in-memory collection with bulk insert for speed.
    """
    if directory is None:
        directory = get_scan_directory()
    
    # Normalize the scan root for consistent storage
    scan_root = normalize_path(directory)
    
    # Validate directory
    if not os.path.exists(directory):
        print(f"  [ERROR] Directory does not exist: {directory}")
        return None
    
    if not os.path.isdir(directory):
        print(f"  [ERROR] Path is not a directory: {directory}")
        return None
    
    print(f"\n{'='*60}")
    print("  DIRECTORY SCAN (FAST MODE)")
    print(f"{'='*60}")
    print(f"  Target: {directory}")
    print(f"  Scan Root: {scan_root}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Initialize database
    init_db()
    
    # Phase 1: Collect all file metadata in memory
    print("  Phase 1: Collecting file metadata...")
    all_files = []
    errors = 0
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # Skip hidden files if configured
            if SKIP_HIDDEN_FILES and filename.startswith('.'):
                continue
            
            filepath = os.path.join(root, filename)
            
            # Progress indicator
            if len(all_files) % PROGRESS_INTERVAL == 0:
                print(f"    Found: {len(all_files):,} files...", end='\r')
            
            # Get metadata
            metadata = get_file_metadata(filepath)
            if metadata is None:
                errors += 1
                continue
            
            all_files.append(metadata)
    
    print(f"    Found: {len(all_files):,} files        ")
    print(f"    Errors: {errors}")
    
    # Phase 2: Bulk database operations
    print(f"\n  Phase 2: Syncing with database...")
    stats = bulk_sync_database(all_files, scan_root)
    stats['scanned'] = len(all_files)
    stats['errors'] = errors
    
    # Print summary
    print(f"\n{'='*60}")
    print("  SCAN COMPLETE")
    print(f"{'='*60}")
    print(f"  Files Scanned:  {stats['scanned']:,}")
    print(f"  New Files:      {stats['inserted']:,}")
    print(f"  Updated:        {stats['updated']:,}")
    print(f"  Restored:       {stats['restored']:,}")
    print(f"  Marked Deleted: {stats['deleted']:,}")
    print(f"  Errors:         {stats['errors']:,}")
    print(f"  Time:           {stats.get('time', 'N/A')}")
    print(f"{'='*60}\n")
    
    return stats


def bulk_sync_database(all_files, scan_root):
    """
    Bulk sync files to database in a single transaction.
    Much faster than individual inserts.
    """
    start_time = datetime.now()
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    stats = {'inserted': 0, 'updated': 0, 'restored': 0, 'deleted': 0}
    
    # Get all existing paths for this scan root
    cursor.execute("""
        SELECT full_path, is_deleted FROM files 
        WHERE scan_root_directory = ?
    """, (scan_root,))
    existing = {row['full_path']: row['is_deleted'] for row in cursor.fetchall()}
    
    scanned_paths = set()
    batch_size = 1000
    batch = []
    
    print(f"    Processing {len(all_files):,} files...")
    
    for i, metadata in enumerate(all_files):
        full_path = metadata['full_path']
        scanned_paths.add(full_path)
        
        if full_path in existing:
            # Existing file - prepare update
            was_deleted = existing[full_path] == 1
            batch.append(('update', metadata, was_deleted))
        else:
            # New file - prepare insert
            batch.append(('insert', metadata, None))
        
        # Process batch
        if len(batch) >= batch_size:
            process_batch(cursor, batch, scan_root, now, stats)
            batch = []
            print(f"    Processed: {i+1:,} / {len(all_files):,}", end='\r')
    
    # Process remaining batch
    if batch:
        process_batch(cursor, batch, scan_root, now, stats)
    
    print(f"    Processed: {len(all_files):,} / {len(all_files):,}        ")
    
    # Mark deleted files (files in DB but not in scan)
    deleted_paths = set(existing.keys()) - scanned_paths
    if deleted_paths:
        print(f"    Marking {len(deleted_paths):,} deleted files...")
        for path in deleted_paths:
            if existing.get(path) == 0:  # Only if not already deleted
                cursor.execute("""
                    UPDATE files SET is_deleted = 1, deleted_at = ?
                    WHERE full_path = ? AND is_deleted = 0
                """, (now, path))
                stats['deleted'] += 1
    
    conn.commit()
    conn.close()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    stats['time'] = f"{elapsed:.1f}s"
    
    return stats


def process_batch(cursor, batch, scan_root, now, stats):
    """Process a batch of insert/update operations."""
    for op_type, metadata, was_deleted in batch:
        if op_type == 'insert':
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
            stats['inserted'] += 1
        else:
            # Update
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
            if was_deleted:
                stats['restored'] += 1
            else:
                stats['updated'] += 1


if __name__ == "__main__":
    # Test scan
    scan_directory()

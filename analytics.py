"""
Directory Analytics CLI Tool - Analytics Module
================================================
SQL-based analytics and insights for fast querying.
Supports lazy hashing for duplicate detection.
All queries filter by current scan root directory.
"""

from database import (
    execute_query, get_connection, get_current_scan_root,
    compute_hashes_for_candidates, get_duplicate_group_stats, get_size_candidates
)
from scanner import format_size
from config import DEFAULT_TOP_N, MAX_SAME_SIZE_FILES


# =============================================================================
# FILE SIZE INSIGHTS
# =============================================================================

def get_top_n_files(n=None, include_deleted=False):
    """Get top N largest files for current scan root."""
    if n is None:
        n = DEFAULT_TOP_N
    
    scan_root = get_current_scan_root()
    
    if include_deleted:
        query = """
            SELECT file_name, file_extension, file_size_bytes, file_size_readable, 
                   full_path, is_deleted
            FROM files
            WHERE scan_root_directory = ?
            ORDER BY file_size_bytes DESC
            LIMIT ?
        """
    else:
        query = """
            SELECT file_name, file_extension, file_size_bytes, file_size_readable, 
                   full_path, is_deleted
            FROM files
            WHERE is_deleted = 0 AND scan_root_directory = ?
            ORDER BY file_size_bytes DESC
            LIMIT ?
        """
    return execute_query(query, (scan_root, n))


def get_smallest_files(n=None):
    """Get N smallest files (excluding zero-byte) for current scan root."""
    if n is None:
        n = DEFAULT_TOP_N
    
    scan_root = get_current_scan_root()
    query = """
        SELECT file_name, file_extension, file_size_bytes, file_size_readable, full_path
        FROM files
        WHERE is_deleted = 0 AND file_size_bytes > 0 AND scan_root_directory = ?
        ORDER BY file_size_bytes ASC
        LIMIT ?
    """
    return execute_query(query, (scan_root, n))


# =============================================================================
# STATISTICS & AGGREGATIONS
# =============================================================================

def get_statistics():
    """Get overall statistics for current scan root."""
    scan_root = get_current_scan_root()
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total active files
    cursor.execute("""
        SELECT COUNT(*) FROM files 
        WHERE is_deleted = 0 AND scan_root_directory = ?
    """, (scan_root,))
    stats['total_files'] = cursor.fetchone()[0]
    
    # Total size
    cursor.execute("""
        SELECT COALESCE(SUM(file_size_bytes), 0) FROM files 
        WHERE is_deleted = 0 AND scan_root_directory = ?
    """, (scan_root,))
    stats['total_size_bytes'] = cursor.fetchone()[0]
    stats['total_size_readable'] = format_size(stats['total_size_bytes'])
    
    # Total deleted files
    cursor.execute("""
        SELECT COUNT(*) FROM files 
        WHERE is_deleted = 1 AND scan_root_directory = ?
    """, (scan_root,))
    stats['deleted_files'] = cursor.fetchone()[0]
    
    # Deleted size
    cursor.execute("""
        SELECT COALESCE(SUM(file_size_bytes), 0) FROM files 
        WHERE is_deleted = 1 AND scan_root_directory = ?
    """, (scan_root,))
    stats['deleted_size_bytes'] = cursor.fetchone()[0]
    stats['deleted_size_readable'] = format_size(stats['deleted_size_bytes'])
    
    # Unique directories
    cursor.execute("""
        SELECT COUNT(DISTINCT parent_directory) FROM files 
        WHERE is_deleted = 0 AND scan_root_directory = ?
    """, (scan_root,))
    stats['total_directories'] = cursor.fetchone()[0]
    
    # Unique file types
    cursor.execute("""
        SELECT COUNT(DISTINCT file_extension) FROM files 
        WHERE is_deleted = 0 AND scan_root_directory = ?
    """, (scan_root,))
    stats['unique_extensions'] = cursor.fetchone()[0]
    
    # Largest file
    cursor.execute("""
        SELECT file_name, file_size_readable 
        FROM files 
        WHERE is_deleted = 0 AND scan_root_directory = ?
        ORDER BY file_size_bytes DESC LIMIT 1
    """, (scan_root,))
    row = cursor.fetchone()
    stats['largest_file'] = (row[0], row[1]) if row else ("N/A", "0 B")
    
    # Smallest non-zero file
    cursor.execute("""
        SELECT file_name, file_size_readable 
        FROM files 
        WHERE is_deleted = 0 AND file_size_bytes > 0 AND scan_root_directory = ?
        ORDER BY file_size_bytes ASC LIMIT 1
    """, (scan_root,))
    row = cursor.fetchone()
    stats['smallest_file'] = (row[0], row[1]) if row else ("N/A", "0 B")
    
    conn.close()
    return stats


def get_type_statistics():
    """Get file count and size grouped by extension for current scan root."""
    scan_root = get_current_scan_root()
    query = """
        SELECT 
            file_extension,
            COUNT(*) as file_count,
            SUM(file_size_bytes) as total_bytes
        FROM files
        WHERE is_deleted = 0 AND scan_root_directory = ?
        GROUP BY file_extension
        ORDER BY total_bytes DESC
    """
    results = execute_query(query, (scan_root,))
    
    # Calculate total for percentages
    total_bytes = sum(row['total_bytes'] or 0 for row in results)
    
    formatted = []
    for row in results:
        bytes_val = row['total_bytes'] or 0
        pct = (bytes_val / total_bytes * 100) if total_bytes > 0 else 0
        formatted.append({
            'extension': row['file_extension'],
            'count': row['file_count'],
            'size_bytes': bytes_val,
            'size_readable': format_size(bytes_val),
            'percentage': f"{pct:.1f}%"
        })
    
    return formatted


# =============================================================================
# DUPLICATE DETECTION (LAZY HASHING)
# =============================================================================

def run_duplicate_detection(progress_callback=None):
    """
    Run lazy hashing to detect duplicates for current scan root.
    Only hashes files that share the same size (potential duplicates).
    Returns: (files_hashed, duplicate_groups_found, stats)
    """
    files_hashed, num_groups = compute_hashes_for_candidates(progress_callback)
    stats = get_duplicate_group_stats()
    return files_hashed, num_groups, stats


def get_potential_duplicate_count():
    """Get count of files that are candidates for duplicate detection (same size)."""
    candidates = get_size_candidates()
    total = sum(len(files) for files in candidates.values())
    return total, len(candidates)


def find_duplicates():
    """Find duplicate files based on hash for current scan root."""
    scan_root = get_current_scan_root()
    query = """
        SELECT duplicate_group, file_hash, COUNT(*) as dup_count
        FROM files
        WHERE is_deleted = 0 AND duplicate_group IS NOT NULL AND scan_root_directory = ?
        GROUP BY duplicate_group
        ORDER BY dup_count DESC
    """
    duplicate_groups = execute_query(query, (scan_root,))
    
    if not duplicate_groups:
        return []
    
    # Get details for each duplicate group
    duplicates = []
    for group_row in duplicate_groups:
        group_id = group_row['duplicate_group']
        detail_query = """
            SELECT file_name, file_size_readable, full_path, file_size_bytes
            FROM files
            WHERE duplicate_group = ? AND is_deleted = 0 AND scan_root_directory = ?
            ORDER BY file_name
        """
        files = execute_query(detail_query, (group_id, scan_root))
        if files:
            duplicates.append({
                'group_id': group_id,
                'hash': group_row['file_hash'][:16] + "..." if group_row['file_hash'] else "N/A",
                'count': group_row['dup_count'],
                'size': files[0]['file_size_readable'],
                'size_bytes': files[0]['file_size_bytes'],
                'files': [dict(f) for f in files]
            })
    
    return duplicates


def get_duplicate_stats():
    """Get summary statistics about duplicates for current scan root."""
    stats = get_duplicate_group_stats()
    return {
        'duplicate_files': stats['duplicate_files'],
        'duplicate_groups': stats['duplicate_groups'],
        'wasted_space': format_size(stats['wasted_bytes'])
    }


# =============================================================================
# SPACE HOG ANALYSIS
# =============================================================================

def get_space_hogs(top_n=10):
    """Get directories consuming most space for current scan root."""
    scan_root = get_current_scan_root()
    query = """
        SELECT 
            parent_directory,
            COUNT(*) as file_count,
            SUM(file_size_bytes) as total_bytes
        FROM files
        WHERE is_deleted = 0 AND scan_root_directory = ?
        GROUP BY parent_directory
        ORDER BY total_bytes DESC
        LIMIT ?
    """
    results = execute_query(query, (scan_root, top_n))
    
    formatted = []
    for row in results:
        formatted.append({
            'directory': row['parent_directory'],
            'file_count': row['file_count'],
            'size_bytes': row['total_bytes'],
            'size_readable': format_size(row['total_bytes'] or 0)
        })
    
    return formatted


# =============================================================================
# CREATIVE INSIGHTS
# =============================================================================

def get_extension_dominance():
    """Get extension dominance ranking with density analysis."""
    stats = get_type_statistics()
    if not stats:
        return []
    
    total_files = sum(s['count'] for s in stats)
    
    for s in stats:
        # File count percentage
        s['count_pct'] = f"{(s['count'] / total_files * 100):.1f}%" if total_files > 0 else "0%"
        # Density = avg file size for that type
        avg_size = s['size_bytes'] / s['count'] if s['count'] > 0 else 0
        s['avg_size'] = format_size(avg_size)
    
    return stats


def get_age_analysis():
    """Analyze files by age (oldest/newest) for current scan root."""
    scan_root = get_current_scan_root()
    
    # Oldest files
    oldest_query = """
        SELECT file_name, modified_timestamp, file_size_readable, full_path
        FROM files
        WHERE is_deleted = 0 AND modified_timestamp IS NOT NULL AND scan_root_directory = ?
        ORDER BY modified_timestamp ASC
        LIMIT 5
    """
    oldest = execute_query(oldest_query, (scan_root,))
    
    # Newest files
    newest_query = """
        SELECT file_name, modified_timestamp, file_size_readable, full_path
        FROM files
        WHERE is_deleted = 0 AND modified_timestamp IS NOT NULL AND scan_root_directory = ?
        ORDER BY modified_timestamp DESC
        LIMIT 5
    """
    newest = execute_query(newest_query, (scan_root,))
    
    return {'oldest': [dict(r) for r in oldest], 'newest': [dict(r) for r in newest]}


def get_zero_byte_files():
    """Find zero-byte (empty) files for current scan root."""
    scan_root = get_current_scan_root()
    query = """
        SELECT file_name, full_path, modified_timestamp
        FROM files
        WHERE is_deleted = 0 AND file_size_bytes = 0 AND scan_root_directory = ?
        ORDER BY file_name
    """
    return execute_query(query, (scan_root,))


def get_deleted_files():
    """Get list of deleted (soft-deleted) files for current scan root."""
    scan_root = get_current_scan_root()
    query = """
        SELECT file_name, file_size_readable, full_path, deleted_at
        FROM files
        WHERE is_deleted = 1 AND scan_root_directory = ?
        ORDER BY deleted_at DESC
    """
    return execute_query(query, (scan_root,))

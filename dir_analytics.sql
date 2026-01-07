-- =============================================================================
-- Directory Analytics CLI Tool - SQL Queries
-- =============================================================================
-- Use these queries in DB Browser for SQLite or any SQLite client
-- Database: Data File/dir_analytics.db
-- =============================================================================

-- #############################################################################
-- CONFIGURATION: Set your scan_root_directory here
-- #############################################################################
-- Change this value to filter by different drives/directories:
--   'D:\'  for D: drive
--   'E:\'  for E: drive
--   'C:\Users\ADMIN\Documents'  for Documents folder
-- 
-- To use: Replace @SCAN_ROOT in queries below, or use the variable method

-- Option 1: Create a temporary table to store the selected root
-- DROP TABLE IF EXISTS config;
-- CREATE TEMP TABLE config (scan_root TEXT);
-- INSERT INTO config VALUES ('D:\');

-- Option 2: Simply replace @SCAN_ROOT with your path in each query

-- For convenience, use Find & Replace:
--   Find: @SCAN_ROOT
--   Replace: 'E:\'  (or your desired path)

-- #############################################################################

-- Current Scan Roots in Database (run this first to see available options)
SELECT 
    scan_root_directory,
    COUNT(*) as file_count,
    SUM(CASE WHEN is_deleted = 0 THEN 1 ELSE 0 END) as active_files,
    printf("%.2f GB", SUM(file_size_bytes) / 1073741824.0) as total_size
FROM files
WHERE scan_root_directory IS NOT NULL
GROUP BY scan_root_directory
ORDER BY file_count DESC;

DECLARE @SCAN_ROOT TEXT;
SET @SCAN_ROOT = 'E:\';
-- SET @SCAN_ROOT = 'D:\';
-- SET @SCAN_ROOT = 'C:\Users\ADMIN\Documents';
-- SET @SCAN_ROOT = 'C:\Users\ADMIN\Downloads';
-- SET @SCAN_ROOT = 'C:\Users\ADMIN\OneDrive\Documents';
-- SET @SCAN_ROOT = 'C:\Users\ADMIN\OneDrive\Desktop';
-- SET @SCAN_ROOT = 'C:\Users\ADMIN\OneDrive\Pictures';

-- -----------------------------------------------------------------------------
-- TOP N LARGEST FILES
-- Replace @SCAN_ROOT with your path, e.g., 'E:\'
-- -----------------------------------------------------------------------------
SELECT 
    file_name,
    file_extension,
    file_size_readable,
    file_size_bytes,
    full_path
FROM files
WHERE is_deleted = 0 
  AND scan_root_directory = @SCAN_ROOT
ORDER BY file_size_bytes DESC
LIMIT 20;

-- -----------------------------------------------------------------------------
-- OVERALL STATISTICS
-- -----------------------------------------------------------------------------
SELECT 
    COUNT(*) as total_files,
    SUM(file_size_bytes) as total_bytes,
    printf("%.2f GB", SUM(file_size_bytes) / 1073741824.0) as total_size
FROM files
WHERE is_deleted = 0
  AND scan_root_directory = @SCAN_ROOT;

-- Unique directories and extensions
SELECT 
    COUNT(DISTINCT parent_directory) as unique_directories,
    COUNT(DISTINCT file_extension) as unique_extensions
FROM files
WHERE is_deleted = 0
  AND scan_root_directory = @SCAN_ROOT;

-- Largest and smallest files
SELECT 'Largest' as type, file_name, file_size_readable
FROM files 
WHERE is_deleted = 0 AND scan_root_directory = @SCAN_ROOT
ORDER BY file_size_bytes DESC LIMIT 1
UNION ALL
SELECT 'Smallest' as type, file_name, file_size_readable
FROM files 
WHERE is_deleted = 0 AND file_size_bytes > 0 AND scan_root_directory = @SCAN_ROOT
ORDER BY file_size_bytes ASC LIMIT 1;

-- -----------------------------------------------------------------------------
-- FILE TYPE ANALYSIS
-- -----------------------------------------------------------------------------
SELECT 
    file_extension,
    COUNT(*) as file_count,
    SUM(file_size_bytes) as total_bytes,
    printf("%.2f MB", SUM(file_size_bytes) / 1048576.0) as total_size,
    printf("%.1f%%", SUM(file_size_bytes) * 100.0 / 
        (SELECT SUM(file_size_bytes) FROM files WHERE is_deleted = 0 AND scan_root_directory = @SCAN_ROOT)) as percentage
FROM files
WHERE is_deleted = 0
  AND scan_root_directory = @SCAN_ROOT
GROUP BY file_extension
ORDER BY total_bytes DESC
LIMIT 30;

-- -----------------------------------------------------------------------------
-- DUPLICATE FILES (by hash)
-- -----------------------------------------------------------------------------
-- Find duplicate groups
SELECT 
    duplicate_group,
    file_hash,
    COUNT(*) as duplicate_count,
    printf("%.2f MB", file_size_bytes / 1048576.0) as file_size
FROM files
WHERE is_deleted = 0 
  AND duplicate_group IS NOT NULL
  AND scan_root_directory = @SCAN_ROOT
GROUP BY duplicate_group
ORDER BY duplicate_count DESC;

-- List all files in duplicate groups
SELECT 
    duplicate_group,
    file_name,
    file_size_readable,
    full_path
FROM files
WHERE is_deleted = 0 
  AND duplicate_group IS NOT NULL
  AND scan_root_directory = @SCAN_ROOT
ORDER BY duplicate_group, file_name;

-- Wasted space from duplicates
SELECT 
    COUNT(*) as total_duplicate_files,
    SUM(wasted) as wasted_bytes,
    printf("%.2f MB", SUM(wasted) / 1048576.0) as wasted_size
FROM (
    SELECT (COUNT(*) - 1) * file_size_bytes as wasted
    FROM files
    WHERE is_deleted = 0 
      AND duplicate_group IS NOT NULL
      AND scan_root_directory = @SCAN_ROOT
    GROUP BY duplicate_group
);

-- -----------------------------------------------------------------------------
-- SPACE HOG DIRECTORIES
-- -----------------------------------------------------------------------------
SELECT 
    parent_directory,
    COUNT(*) as file_count,
    SUM(file_size_bytes) as total_bytes,
    printf("%.2f MB", SUM(file_size_bytes) / 1048576.0) as total_size
FROM files
WHERE is_deleted = 0
  AND scan_root_directory = @SCAN_ROOT
GROUP BY parent_directory
ORDER BY total_bytes DESC
LIMIT 20;

-- -----------------------------------------------------------------------------
-- FILE AGE ANALYSIS
-- -----------------------------------------------------------------------------
-- Oldest files
SELECT 
    file_name,
    modified_timestamp,
    file_size_readable,
    full_path
FROM files
WHERE is_deleted = 0 
  AND modified_timestamp IS NOT NULL
  AND scan_root_directory = @SCAN_ROOT
ORDER BY modified_timestamp ASC
LIMIT 10;

-- Newest files
SELECT 
    file_name,
    modified_timestamp,
    file_size_readable,
    full_path
FROM files
WHERE is_deleted = 0 
  AND modified_timestamp IS NOT NULL
  AND scan_root_directory = @SCAN_ROOT
ORDER BY modified_timestamp DESC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- ZERO-BYTE (EMPTY) FILES
-- -----------------------------------------------------------------------------
SELECT 
    file_name,
    full_path,
    modified_timestamp
FROM files
WHERE is_deleted = 0 
  AND file_size_bytes = 0
  AND scan_root_directory = @SCAN_ROOT
ORDER BY file_name;

-- -----------------------------------------------------------------------------
-- DELETED FILES (SOFT DELETE TRACKING)
-- -----------------------------------------------------------------------------
SELECT 
    file_name,
    file_size_readable,
    full_path,
    deleted_at
FROM files
WHERE is_deleted = 1
  AND scan_root_directory = @SCAN_ROOT
ORDER BY deleted_at DESC;

-- -----------------------------------------------------------------------------
-- EXTENSION DOMINANCE RANKING
-- -----------------------------------------------------------------------------
SELECT 
    file_extension,
    COUNT(*) as count,
    printf("%.1f%%", COUNT(*) * 100.0 / 
        (SELECT COUNT(*) FROM files WHERE is_deleted = 0 AND scan_root_directory = @SCAN_ROOT)) as count_pct,
    SUM(file_size_bytes) as size_bytes,
    printf("%.2f MB", SUM(file_size_bytes) / 1048576.0) as total_size,
    printf("%.1f%%", SUM(file_size_bytes) * 100.0 / 
        (SELECT SUM(file_size_bytes) FROM files WHERE is_deleted = 0 AND scan_root_directory = @SCAN_ROOT)) as size_pct,
    printf("%.2f KB", AVG(file_size_bytes) / 1024.0) as avg_size
FROM files
WHERE is_deleted = 0
  AND scan_root_directory = @SCAN_ROOT
GROUP BY file_extension
ORDER BY size_bytes DESC;

-- -----------------------------------------------------------------------------
-- ALL SCAN ROOTS SUMMARY (No filter needed)
-- -----------------------------------------------------------------------------
SELECT 
    scan_root_directory,
    COUNT(*) as file_count,
    SUM(CASE WHEN is_deleted = 0 THEN 1 ELSE 0 END) as active_files,
    SUM(CASE WHEN is_deleted = 1 THEN 1 ELSE 0 END) as deleted_files,
    printf("%.2f GB", SUM(file_size_bytes) / 1073741824.0) as total_size
FROM files
GROUP BY scan_root_directory
ORDER BY file_count DESC;

-- -----------------------------------------------------------------------------
-- POTENTIAL DUPLICATES (Same Size - Before Hashing)
-- -----------------------------------------------------------------------------
SELECT 
    file_size_bytes,
    file_size_readable,
    COUNT(*) as same_size_count
FROM files
WHERE is_deleted = 0 
  AND file_size_bytes > 0
  AND scan_root_directory = @SCAN_ROOT
GROUP BY file_size_bytes
HAVING COUNT(*) > 1
ORDER BY same_size_count DESC
LIMIT 50;

-- -----------------------------------------------------------------------------
-- RECENT ACTIVITY (Files seen in last scan)
-- -----------------------------------------------------------------------------
SELECT 
    file_name,
    file_size_readable,
    last_seen,
    full_path
FROM files
WHERE is_deleted = 0
  AND scan_root_directory = @SCAN_ROOT
ORDER BY last_seen DESC
LIMIT 50;

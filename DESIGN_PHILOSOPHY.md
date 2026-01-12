# DESIGN_PHILOSOPHY

## The Problem

**Managing large directories is painful.** Questions like:
- "Where is all my disk space going?"
- "Do I have duplicate files wasting space?"
- "What are my largest files?"
- "Which file types dominate my storage?"

These questions require scanning thousands of files - a slow process that existing tools either:
1. Do **too slowly** (hashing every file)
2. Do **incompletely** (no duplicate detection)
3. Require **expensive software** (disk analyzers)

## The Solution

**Directory Analytics CLI Tool** - A fast, free, Python-based scanner that:
- Scans at **near-native speed** (25,000+ files/second)
- Uses **lazy hashing** (only hash when needed)
- Stores data in **SQLite** (query anything, anytime)
- Tracks **multiple directories** (switch without rescanning)
- Provides **9 analytics views** (answer common questions instantly)

## Key Design Decisions

### 1. In-Memory Collection + Bulk Insert
Instead of writing each file to database individually (slow!), we:
1. Collect all metadata in memory
2. Write everything in one transaction

**Result**: 100x faster than per-file commits.

### 2. Lazy Hashing
Hashing every file is expensive. Instead:
1. Scan stores metadata only (fast)
2. Find files with same size (potential duplicates)
3. Hash only those candidates when user requests

**Result**: 10-50x faster scans.

### 3. Multi-Directory Support
Each file stores its `scan_root_directory`. When you switch directories:
- Old data stays in database
- Analytics filter to current directory only
- No data loss, no confusion

### 4. Soft Delete Tracking
When files disappear from disk:
- Mark as `is_deleted = 1`
- Track deletion timestamp
- Keep historical record

## Use Cases

| User | Need | Solution |
|------|------|----------|
| Developer | "Find large files in project" | Top N Files + File Type Analysis |
| IT Admin | "Audit shared drives" | Space Hog Directories |
| Anyone | "Find duplicate photos/videos" | Duplicate Detection |
| Archivist | "Track file changes over time" | Deleted Files + Timestamps |

## Target Audience

- Windows users with large file collections
- Anyone who wants to understand their disk usage
- Users who prefer CLI tools over GUIs
- Developers who want to extend the tool

## What This Is NOT

- Not a file manager (doesn't move/delete files)
- Not a backup tool (only analyzes, doesn't copy)
- Not cross-platform (Windows-focused)
- Not a real-time monitor (manual rescan needed)

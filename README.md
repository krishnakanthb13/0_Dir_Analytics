# Directory Analytics CLI Tool

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A fast, production-ready CLI tool for directory scanning, file analytics, and duplicate detection.

## 📖 Documentation

- [Design Philosophy](DESIGN_PHILOSOPHY.md) - Rationale and design decisions
- [Code Documentation](CODE_DOCUMENTATION.md) - Technical architecture and API
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to the project

## Features

- 🚀 **Fast Scanning** - In-memory collection with bulk database insert (~25,000 files/second)
- 🔍 **Lazy Hashing** - Hash only potential duplicates, not every file
- 📊 **9 Analytics Views** - Size analysis, duplicates, file types, age, and more
- 🔄 **Multi-Directory** - Switch between directories without losing data
- 📁 **SQLite Storage** - Fast queries with indexed columns
- 📝 **Session Logging** - All actions logged with timestamps
- 🗑️ **Soft Delete Tracking** - Track files removed from disk

## Quick Start

1. **Configure directories** in `config.py`:
   ```python
    SCAN_DIRECTORIES = [
        r"D:\\",
        r"E:\\",
       r"C:\Users\ADMIN\Documents",
    ]
   ```

2. **Run the tool**:
   ```cmd
   Dir_Analytics.bat
   ```

3. **Select option 1** to scan, then **option 2** for analytics.

## Menu Options

| # | Option | Description |
|---|--------|-------------|
| 1 | Scan Directory | Fast metadata scan of current directory |
| 2 | View Analytics | 9 different analysis views |
| 3 | Export to CSV | Backup data to CSV file |
| 4 | Switch Directory | Change active directory |
| 5 | Open in DB Browser | Open database in SQLite browser |
| 6 | Compact Database | Run VACUUM to reclaim space |
| 7 | Exit | Close the application |

## Analytics Views

| View | Description |
|------|-------------|
| Top N Largest Files | Find space hogs |
| Overall Statistics | Total files, size, unique paths |
| File Type Analysis | Breakdown by extension |
| Duplicate Files | Files with same hash (lazy computed) |
| Space Hog Directories | Directories using most space |
| File Age Analysis | Oldest and newest files |
| Zero-Byte Files | Empty files |
| Deleted Files | Files removed since last scan |
| Extension Dominance | Extension ranking with avg sizes |

## Configuration

Edit `config.py`:

```python
# Directories to scan
SCAN_DIRECTORIES = [r"D:\\", r"E:\\"]

# Lazy hashing limits
MAX_SAME_SIZE_FILES = 100   # Skip if >100 files share same size
MIN_FILE_SIZE_FOR_HASH = 1  # Skip empty files

# DB Browser path (for Open in DB Browser option)
DB_BROWSER_PATH = r"C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe"
```

## Data Storage

All data stored in `Data File/` folder:
- `dir_analytics.db` - SQLite database
- `session_*.log` - Session logs
- `export_*.csv` - CSV exports

## SQL Queries

Use `dir_analytics.sql` for direct database queries. Replace `@SCAN_ROOT` with your path:
```sql
-- Example: Find largest files in E: drive
SELECT * FROM files 
WHERE scan_root_directory = 'E:\' 
ORDER BY file_size_bytes DESC LIMIT 20;
```

## Requirements

- Python 3.6+
- Windows OS
- No external dependencies

## License

GNU General Public License v3.0 - See [LICENSE](LICENSE)

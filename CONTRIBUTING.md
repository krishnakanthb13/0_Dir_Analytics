# Contributing to Directory Analytics CLI Tool

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs
1. Check if the issue already exists
2. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your Python version and OS

### Suggesting Features
1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Discuss implementation approach

### Pull Requests
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push and create a Pull Request

## Code Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to functions
- Keep functions focused and small
- Use meaningful variable names
- Comment complex logic

## Project Structure

```
Dir_Analytics/
├── config.py          # Configuration settings
├── database.py        # SQLite operations
├── scanner.py         # Directory scanning
├── analytics.py       # Analytics queries
├── cli_menu.py        # CLI interface
├── logger.py          # Session logging
├── dir_analytics.py   # Main entry point
├── dir_analytics.sql  # SQL query reference
└── Dir_Analytics.bat  # Windows launcher
```

## Testing

Before submitting:
1. Run a scan on a test directory
2. Test all analytics options
3. Verify CSV export works
4. Check logging output

## Questions?

Open an issue or start a discussion!

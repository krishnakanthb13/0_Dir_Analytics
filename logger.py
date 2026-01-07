"""
Directory Analytics CLI Tool - Logger Module
=============================================
Captures all console output and logs to file with timestamps.
"""

import sys
import os
from datetime import datetime
from config import DATA_FOLDER


class Logger:
    """
    Dual-output logger that writes to both console and log file.
    Captures all print() output automatically.
    """
    
    def __init__(self, log_file=None):
        self.terminal = sys.stdout
        self.log_file = log_file
        self.file_handle = None
        
        if log_file:
            self.start_logging(log_file)
    
    def start_logging(self, log_file=None):
        """Start logging to file."""
        if log_file is None:
            # Create log file in Data File folder
            os.makedirs(DATA_FOLDER, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(DATA_FOLDER, f"session_{timestamp}.log")
        
        self.log_file = log_file
        
        # Open file in append mode
        self.file_handle = open(log_file, 'a', encoding='utf-8')
        
        # Write session header
        self.file_handle.write(f"\n{'='*60}\n")
        self.file_handle.write(f"  SESSION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.file_handle.write(f"{'='*60}\n\n")
        self.file_handle.flush()
        
        # Redirect stdout
        sys.stdout = self
    
    def stop_logging(self):
        """Stop logging and restore stdout."""
        if self.file_handle:
            self.file_handle.write(f"\n{'='*60}\n")
            self.file_handle.write(f"  SESSION ENDED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.file_handle.write(f"{'='*60}\n")
            self.file_handle.close()
            self.file_handle = None
        sys.stdout = self.terminal
    
    def write(self, message):
        """Write to both terminal and log file."""
        # Write to terminal
        self.terminal.write(message)
        
        # Write to log file with timestamp for new lines
        if self.file_handle and message.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            # Add timestamp to each line
            lines = message.split('\n')
            for line in lines:
                if line.strip():
                    self.file_handle.write(f"[{timestamp}] {line}\n")
            self.file_handle.flush()
    
    def flush(self):
        """Flush both outputs."""
        self.terminal.flush()
        if self.file_handle:
            self.file_handle.flush()


# Global logger instance
_logger = None


def start_logging():
    """Start the global logger."""
    global _logger
    if _logger is None:
        _logger = Logger()
        _logger.start_logging()
        return _logger.log_file
    return _logger.log_file


def stop_logging():
    """Stop the global logger."""
    global _logger
    if _logger:
        _logger.stop_logging()
        _logger = None


def get_log_file():
    """Get the current log file path."""
    global _logger
    if _logger:
        return _logger.log_file
    return None


def log_action(action):
    """Log a user action with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n  >>> Action: {action}")

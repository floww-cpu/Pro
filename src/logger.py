"""
Prometheus Logger
Provides logging functionality with color support
"""

from enum import IntEnum
import sys


class LogLevel(IntEnum):
    """Log levels"""
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


class Colors:
    """ANSI color codes"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


class Logger:
    """Logger class for Prometheus"""
    
    def __init__(self):
        self.log_level = LogLevel.INFO
        self.colors_enabled = True
    
    def _color(self, text, color):
        """Apply color to text if colors are enabled"""
        if self.colors_enabled:
            return f"{color}{text}{Colors.RESET}"
        return text
    
    def debug(self, message):
        """Log debug message"""
        if self.log_level <= LogLevel.DEBUG:
            print(self._color(f"[DEBUG] {message}", Colors.CYAN))
    
    def info(self, message):
        """Log info message"""
        if self.log_level <= LogLevel.INFO:
            print(self._color(f"[INFO] {message}", Colors.GREEN))
    
    def warn(self, message):
        """Log warning message"""
        if self.log_level <= LogLevel.WARN:
            print(self._color(f"[WARN] {message}", Colors.YELLOW))
    
    def error(self, message):
        """Log error message and exit"""
        print(self._color(f"[ERROR] {message}", Colors.RED), file=sys.stderr)
        sys.exit(1)

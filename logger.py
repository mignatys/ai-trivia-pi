"""
logger.py
---------
Central logging utility used by all modules.

Supports:
- Colored console logs
- JSON-structured log history (for web interface)
- Simple API: log.info(), log.warn(), log.error(), log.debug()
"""

import json
import time
import threading
import sys # Import sys for stdout.flush()
from config import LOG_LEVEL # Import LOG_LEVEL from config.py

class Logger:
    def __init__(self):
        self.lock = threading.Lock()
        self.history = []  # entries for web interface (max 300)
        self.level_map = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
        self.current_log_level = self.level_map.get(LOG_LEVEL.upper(), 0) # Default to DEBUG if not found

    # Color codes
    COLOR_RESET = "\033[0m"
    COLORS = {
        "INFO": "\033[92m",
        "WARN": "\033[93m",
        "ERROR": "\033[91m",
        "DEBUG": "\033[94m",
    }

    def _should_log(self, level):
        return self.level_map.get(level.upper(), 0) >= self.current_log_level

    def _store(self, level, msg):
        entry = {
            "timestamp": time.time(),
            "level": level,
            "message": msg,
        }
        with self.lock:
            self.history.append(entry)
            # keep memory small
            if len(self.history) > 300:
                self.history.pop(0)

    def _print(self, level, msg):
        if self._should_log(level):
            color = self.COLORS.get(level, "")
            print(f"{color}[{level}] {msg}{self.COLOR_RESET}")
            sys.stdout.flush() # Explicitly flush stdout

    def log(self, level, msg):
        self._store(level, msg)
        self._print(level, msg)

    # Convenience methods
    def info(self, msg):  self.log("INFO", msg)
    def warn(self, msg):  self.log("WARN", msg)
    def error(self, msg): self.log("ERROR", msg)
    def debug(self, msg): self.log("DEBUG", msg)


# Global logger instance
log = Logger()

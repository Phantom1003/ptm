"""
Module for logging functionality in PTM.
"""

import os
import datetime
from typing import Callable, Any, Optional


class PTMLogger:
    """
    Logger class for PTM with configurable log levels and handlers.
    """
    
    def __init__(self, level: str = "INFO", log_handler: Optional[Callable[[str, Any], None]] = None):
        """
        Initialize the logger.
        
        Args:
            level: The minimum log level to display (QUIET, DEBUG, INFO, WARNING, ERROR)
            log_handler: Optional custom log handler function
        """
        self.levels = ["QUIET", "DEBUG", "INFO", "WARNING", "ERROR"]
        self.level = level if level in self.levels else "INFO"
        self.log_handler = log_handler or self.default_handler

    def verbose(self, level: str) -> bool:
        """
        Check if a log level should be displayed.
        
        Args:
            level: The log level to check
            
        Returns:
            bool: True if the level should be displayed
        """
        return self.levels.index(level) >= self.levels.index(self.level)

    def default_handler(self, level: str, *message: Any) -> None:
        """
        Default log handler that prints to stdout.
        
        Args:
            level: The log level
            *message: Variable number of message parts
        """
        if not self.verbose(level):
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {' '.join(map(str, message))}")

    def log(self, level: str, *message: Any) -> None:
        """
        Log a message at the specified level.
        
        Args:
            level: The log level
            *message: Variable number of message parts
        """
        self.log_handler(level, *message)

    def info(self, *message: Any) -> None:
        """
        Log an info message.
        
        Args:
            *message: Variable number of message parts
        """
        self.log("INFO", *message)
        
    def debug(self, *message: Any) -> None:
        """
        Log a debug message.
        
        Args:
            *message: Variable number of message parts
        """
        self.log("DEBUG", *message)
        
    def warning(self, *message: Any) -> None:
        """
        Log a warning message.
        
        Args:
            *message: Variable number of message parts
        """
        self.log("WARNING", *message)
        
    def error(self, *message: Any) -> None:
        """
        Log an error message.
        
        Args:
            *message: Variable number of message parts
        """
        self.log("ERROR", *message)


# Create a global logger instance
plog = PTMLogger(os.getenv("PTM_LOG_LEVEL", "INFO"))

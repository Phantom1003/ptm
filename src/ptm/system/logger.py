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
    
    def __init__(self, verbose_level: str = "INFO", log_handler: Optional[Callable[[str, Any], None]] = None):
        """
        Initialize the logger.
        
        Args:
            level: The minimum log level to display (QUIET, DEBUG, INFO, WARNING, ERROR)
            log_handler: Optional custom log handler function
        """
        self.levels = ["QUIET", "DEBUG", "INFO", "WARNING", "ERROR"]
        self.verbose_level = verbose_level if verbose_level in self.levels else "INFO"
        self.log_handler = log_handler or self.default_handler

    def verbose(self, level: str) -> bool:
        """
        Check if a log level should be displayed.
        
        Args:
            level: The log level to check
            
        Returns:
            bool: True if the level should be displayed
        """
        return self.levels.index(level) >= self.levels.index(self.verbose_level)

    def format(self, *message: Any) -> str:
        return ' '.join(map(str, message))
    
    def prefix(self, level: str) -> str:
        return f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}]"

    def default_handler(self, content: str) -> None:
        print(content)

    def info(self, *message: Any) -> None:
        if not self.verbose("INFO"):
            return

        content = self.format(*message)
        self.log_handler(content)
        
    def debug(self, *message: Any) -> None:
        if not self.verbose("DEBUG"):
            return

        content = self.format(*message)
        self.log_handler(content)
        
    def warning(self, *message: Any) -> None:
        if not self.verbose("WARNING"):
            return

        content = self.format(*message)
        self.log_handler(content)
        
    def error(self, *message: Any) -> None:
        if not self.verbose("ERROR"):
            return

        content = self.format(*message)
        self.log_handler(content)


# Create a global logger instance
plog = PTMLogger(os.getenv("PTM_LOG_LEVEL", "INFO"))

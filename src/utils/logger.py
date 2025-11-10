"""Logging utilities for the Creative Automation Pipeline."""

import logging
import sys
from pathlib import Path
from typing import Optional


class PipelineLogger:
    """Logger for pipeline operations with console and file output."""
    
    def __init__(self, log_file: Optional[str] = None, level: str = "INFO"):
        """
        Initialize the pipeline logger.
        
        Args:
            log_file: Path to log file. If None, logs only to console.
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger("CreativeAutomationPipeline")
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if log_file specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_operation(self, operation: str, status: str, details: Optional[dict] = None):
        """
        Log an individual operation.
        
        Args:
            operation: Description of the operation
            status: Status of the operation (success, failure, warning, etc.)
            details: Optional dictionary with additional details
        """
        message = f"{operation} - Status: {status}"
        
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" - {detail_str}"
        
        # Determine log level based on status
        status_lower = status.lower()
        if status_lower in ["success", "complete", "completed"]:
            self.logger.info(message)
        elif status_lower in ["warning", "warn", "skipped"]:
            self.logger.warning(message)
        elif status_lower in ["error", "failed", "failure"]:
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)

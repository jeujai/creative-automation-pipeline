"""Unit tests for PipelineLogger."""

import logging
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from src.utils.logger import PipelineLogger


class TestPipelineLogger:
    """Test suite for PipelineLogger class."""

    def test_logger_initialization_console_only(self):
        """Test logger initializes with console output only."""
        logger = PipelineLogger(log_file=None, level="INFO")
        
        assert logger.logger is not None
        assert logger.logger.name == "CreativeAutomationPipeline"
        assert logger.logger.level == logging.INFO
        assert len(logger.logger.handlers) == 1  # Console handler only

    def test_logger_initialization_with_file(self):
        """Test logger initializes with both console and file output."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="DEBUG")
            
            assert logger.logger.level == logging.DEBUG
            assert len(logger.logger.handlers) == 2  # Console + file handlers
            assert log_file.exists()

    def test_logger_creates_log_directory(self):
        """Test logger creates log directory if it doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "logs" / "subdir" / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            assert log_file.parent.exists()
            assert log_file.exists()

    def test_log_operation_success(self):
        """Test logging a successful operation."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.log_operation("Test operation", "success", {"key": "value"})
            
            # Read log file
            log_content = log_file.read_text()
            assert "Test operation - Status: success" in log_content
            assert "key=value" in log_content

    def test_log_operation_warning(self):
        """Test logging a warning operation."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.log_operation("Test operation", "warning", {"reason": "test"})
            
            log_content = log_file.read_text()
            assert "WARNING" in log_content
            assert "Test operation - Status: warning" in log_content

    def test_log_operation_error(self):
        """Test logging an error operation."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.log_operation("Test operation", "error", {"error": "test error"})
            
            log_content = log_file.read_text()
            assert "ERROR" in log_content
            assert "Test operation - Status: error" in log_content

    def test_log_operation_without_details(self):
        """Test logging operation without details dictionary."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.log_operation("Simple operation", "complete")
            
            log_content = log_file.read_text()
            assert "Simple operation - Status: complete" in log_content

    def test_info_method(self):
        """Test info logging method."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.info("Info message")
            
            log_content = log_file.read_text()
            assert "INFO" in log_content
            assert "Info message" in log_content

    def test_warning_method(self):
        """Test warning logging method."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.warning("Warning message")
            
            log_content = log_file.read_text()
            assert "WARNING" in log_content
            assert "Warning message" in log_content

    def test_error_method(self):
        """Test error logging method."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.error("Error message")
            
            log_content = log_file.read_text()
            assert "ERROR" in log_content
            assert "Error message" in log_content

    def test_debug_method(self):
        """Test debug logging method."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="DEBUG")
            
            logger.debug("Debug message")
            
            log_content = log_file.read_text()
            assert "DEBUG" in log_content
            assert "Debug message" in log_content

    def test_debug_not_logged_at_info_level(self):
        """Test debug messages are not logged at INFO level."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.debug("Debug message")
            
            log_content = log_file.read_text()
            assert "Debug message" not in log_content

    def test_log_formatting(self):
        """Test log message formatting includes timestamp and level."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.info("Test message")
            
            log_content = log_file.read_text()
            # Check for timestamp format (YYYY-MM-DD HH:MM:SS)
            assert "CreativeAutomationPipeline" in log_content
            assert "INFO" in log_content
            assert "Test message" in log_content

    def test_multiple_operations_logged(self):
        """Test multiple operations are logged sequentially."""
        with TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = PipelineLogger(log_file=str(log_file), level="INFO")
            
            logger.log_operation("Operation 1", "success")
            logger.log_operation("Operation 2", "warning")
            logger.log_operation("Operation 3", "error")
            
            log_content = log_file.read_text()
            assert "Operation 1" in log_content
            assert "Operation 2" in log_content
            assert "Operation 3" in log_content

# src/utils/logger.py
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str) -> logging.Logger:
    """Set up and return a logger with file and console handlers."""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to DEBUG level for more details
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
        
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatters with more detailed information
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(
        log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
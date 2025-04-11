"""
Logging configuration for the application
"""
import os
import logging
import logging.handlers
from app.config import get_settings

def setup_logger():
    """
    Configure and return a logger instance for the application
    """
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Get settings
    settings = get_settings()
    
    # Configure logger
    logger = logging.getLogger("sftp_client")
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Add rotating file handler
    rf_handler = logging.handlers.TimedRotatingFileHandler(
        f"{logs_dir}/sftp_client.log", 
        when='midnight', 
        interval=1, 
        backupCount=7
    )
    rf_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(rf_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)
    
    return logger

def get_logger():
    """
    Return the application logger
    """
    return logging.getLogger("sftp_client")
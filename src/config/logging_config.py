"""Logging configuration for the parliamentary network analysis application."""
import logging


def setup_logger(module_name: str) -> logging.Logger:
    """Configure and return a logger instance for a given module.
    
    Args:
        module_name: Module name (typically __name__)
        
    Returns:
        Configured Logger instance
        
    Example:
        logger = setup_logger(__name__)
        logger.info("Processing started")
    """
    logger = logging.getLogger(module_name)
    
    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
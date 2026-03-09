import logging


def setup_logger(name: str) -> logging.Logger:
    """
    Configura um logger para o módulo especificado.
    
    Args:
        name: Nome do módulo (__name__)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
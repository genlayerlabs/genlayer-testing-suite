import logging


def setup_logger() -> logging.Logger:
    """Setup a logger for the gltest package - disabled by default"""

    logger = logging.getLogger("gltest")

    logger.setLevel(logging.NOTSET)
    logger.disabled = True
    logger.addHandler(logging.NullHandler())
    return logger


logger = setup_logger()

__all__ = ["logger"]

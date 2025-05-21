import logging
from colorama import Fore, Style, init


init()


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to the log levels"""

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{Style.RESET_ALL}"
            )
        return super().format(record)


def setup_logger():
    logger = logging.getLogger("gltest")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = ColoredFormatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger


logger = setup_logger()

__all__ = ["logger"]

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
        levelname_plain = record.levelname
        if levelname_plain in self.COLORS:
            colored = (
                f"{self.COLORS[levelname_plain]}{levelname_plain}{Style.RESET_ALL}"
            )
            record.levelname = colored
            formatted = super().format(record)
            record.levelname = levelname_plain
            return formatted
        return super().format(record)


def setup_logger():
    logger = logging.getLogger("gltest_cli")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = ColoredFormatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger


logger = setup_logger()

__all__ = ["logger"]

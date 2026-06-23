import os
import logging
import sys

class AppLogger:
    _logger = None

    @staticmethod
    def configure(log_file: str | None = None):
        handlers = [logging.StreamHandler(sys.stdout)]

        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True) if os.path.dirname(log_file) else None
            handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=handlers
        )

        AppLogger._logger = logging.getLogger("AppLogger")

    @staticmethod
    def info(message: str, *args, **kwargs):
        AppLogger._logger.info(message, *args, **kwargs)

    @staticmethod
    def warning(message: str, *args, **kwargs):
        AppLogger._logger.warning(message, *args, **kwargs)

    @staticmethod
    def error(message: str, *args, **kwargs):
        AppLogger._logger.error(message, *args, **kwargs)

    @staticmethod
    def debug(message: str, *args, **kwargs):
        AppLogger._logger.debug(message, *args, **kwargs)

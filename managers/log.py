import logging
import os
from datetime import datetime
from typing import Dict

from mixins.singleton import Singleton


class LogManager(Singleton):
    def __setup__(self, debug_mode: bool = True, testing_mode: bool = False) -> None:
        self.debug_mode: bool = debug_mode
        self.testing_mode: bool = testing_mode
        self.loggers: Dict[str, logging.Logger] = {}
        self.base_logger = logging.getLogger(name="SCIV")
        self.setup_loggers()

    def setup_loggers(self) -> None:
        log_types: Dict[str, int] = {
            "gameplay": logging.DEBUG,
            "engine": logging.DEBUG,
            "graphics": logging.DEBUG,
            "misc": logging.DEBUG,
            "debug": logging.DEBUG,
        }

        for log_type, level in log_types.items():
            logger: logging.Logger = self.base_logger.getChild(log_type)
            logger.setLevel(level=level)

            # Remove all handlers associated with the logger
            for handler in logger.handlers[:]:
                logger.removeHandler(hdlr=handler)

            # Create log directory structure
            log_dir: str = f"logs/{log_type}"
            os.makedirs(name=log_dir, exist_ok=True)
            log_file_name: str = f"log_{datetime.now().timestamp()}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
            log_file: str = os.path.join(log_dir, log_file_name)

            # Create file handler
            file_handler = logging.FileHandler(filename=log_file)
            file_handler.setLevel(level=level)

            # Create formatter and add it to the handlers
            formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(fmt=formatter)
            logger.addHandler(hdlr=file_handler)

            # Add stream handler if in debug mode and not testing mode

            self.loggers[log_type] = logger

    def log(self, log_type: str, message: str):
        if log_type in self.loggers:
            self.loggers[log_type].info(message)
        else:
            raise ValueError(f"Unknown log type: {log_type}")

    def error(self, log_type: str, message: str) -> None:
        if log_type in self.loggers:
            self.loggers[log_type].error(msg=message)
        else:
            raise ValueError(f"Unknown log type: {log_type}")

    def logger(self, logger_key: str) -> logging.Logger:
        return self.loggers[logger_key]

    def set_testing_mode(self, testing_mode: bool) -> None:
        """
        Sets the testing mode and reconfigures the loggers and output redirection.

        Args:
            testing_mode (bool): Flag to enable or disable testing mode.
        """
        self.testing_mode = testing_mode
        self.setup_loggers()

    @property
    def gameplay(self) -> logging.Logger:
        return self.loggers["gameplay"]

    @property
    def engine(self) -> logging.Logger:
        return self.loggers["engine"]

    @property
    def graphics(self) -> logging.Logger:
        return self.loggers["graphics"]

    @property
    def misc(self) -> logging.Logger:
        return self.loggers["misc"]

    @property
    def debug(self) -> logging.Logger:
        return self.loggers["debug"]

import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple

from helpers.collection import BoundedStack
from mixins.singleton import Singleton

try:
    from kivy.clock import Clock
except ModuleNotFoundError:
    class _FallbackClock:
        @staticmethod
        def schedule_once(callback: Callable[[float], None], timeout: float = 0.0) -> None:
            callback(timeout)

    Clock = _FallbackClock()


class UILogHandler(logging.Handler):
    ALL_MARKER = "ALL"
    LOG_LIMIT = 1000

    records: BoundedStack[Tuple[int, str, str]] = BoundedStack(limit=LOG_LIMIT)

    def __init__(self, on_log: Callable[[datetime, str, str], None] | None = None) -> None:
        super().__init__()
        self.on_log: Callable[[datetime, str, str], None] | None = on_log

    def emit(self, record: logging.LogRecord) -> None:
        msg: str = self.format(record)
        Clock.schedule_once(lambda dt: self._on_clock_tick(dt, record, msg), 0)  # type:ignore

    def _on_clock_tick(self, dt: Any, record: logging.LogRecord, message: str) -> None:
        self._add_record(record.levelname, message)

    def _add_record(self, level: str, msg: str) -> None:
        now: datetime = datetime.now()
        self.records.push((int(now.timestamp()), level, msg))

        if hasattr(self, "on_log") and callable(self.on_log):
            self.on_log(now, level, msg)

    def _filter_get_records(self, severity: str) -> List[Tuple[int, str, str]]:
        if severity == self.ALL_MARKER:
            return self.records.to_list()
        return [record for record in self.records if record[1] == severity]

    def get_all_records(self) -> List[Tuple[int, str, str]]:
        return self.records.to_list()

    def last_record(self, severity: str = ALL_MARKER) -> Tuple[int, str, str]:
        result: List[Tuple[int, str, str]] = self.last_records(1, severity)
        return result[0] if result else (0, "", "")

    def last_records(self, count: int, severity: str = ALL_MARKER) -> List[Tuple[int, str, str]]:
        filtered_records: List[Tuple[int, str, str]] = self._filter_get_records(severity)
        return filtered_records[-count:] if len(filtered_records) >= count else filtered_records


class LogManager(Singleton):
    def __setup__(self, debug_mode: bool = True, testing_mode: bool = False) -> None:
        from system.vars import APPLICATION_NAME

        self.debug_mode: bool = debug_mode
        self.testing_mode: bool = testing_mode
        self.loggers: Dict[str, logging.Logger] = {}
        self.base_logger: logging.Logger = logging.getLogger(name=APPLICATION_NAME.lower())
        self.ui_handler = UILogHandler()
        self.setup_loggers()

    def setup_loggers(self) -> None:
        from helpers.paths import PathsHelper

        self.base_logger.addHandler(self.ui_handler)

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

            base_path = PathsHelper.get_data_dir()

            log_dir: str = f"{base_path}/logs/{log_type}"
            os.makedirs(name=log_dir, exist_ok=True)
            log_file_name: str = f"log_{datetime.now().timestamp()}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
            log_file: str = os.path.join(log_dir, log_file_name)

            file_handler = logging.FileHandler(filename=log_file)
            file_handler.setLevel(level=level)

            formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(fmt=formatter)
            logger.addHandler(hdlr=file_handler)
            logger.addHandler(hdlr=self.ui_handler)

            self.loggers[log_type] = logger

    def get_logger(self, log_type: str) -> logging.Logger:
        if log_type in self.loggers:
            return self.loggers[log_type]
        else:
            raise ValueError(f"Unknown log type: {log_type}")

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

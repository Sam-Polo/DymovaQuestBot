import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

_MSK = ZoneInfo("Europe/Moscow")


class MoscowTimeFormatter(logging.Formatter):
    def __init__(self, app_version: str, fmt: str | None = None, datefmt: str | None = None) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._app_version = app_version

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=_MSK)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="seconds")

    def format(self, record: logging.LogRecord) -> str:
        # версия в каждой строке без filters на root (дочерние логгеры иначе теряют поле)
        record.app_version = self._app_version
        return super().format(record)


def setup_logging(app_version: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        MoscowTimeFormatter(
            app_version=app_version,
            fmt="%(asctime)s MSK [%(levelname)s] v=%(app_version)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

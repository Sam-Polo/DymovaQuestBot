from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_MSK = ZoneInfo("Europe/Moscow")


def now_msk() -> datetime:
    return datetime.now(_MSK)


def msk_date_str(dt: datetime | None = None) -> str:
    # дата по МСК для лимита вопросов и отчётов
    if dt is None:
        dt = now_msk()
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=_MSK)
    else:
        dt = dt.astimezone(_MSK)
    return dt.strftime("%Y-%m-%d")


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

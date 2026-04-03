import os
from dataclasses import dataclass
from functools import lru_cache

from quest_bot import __version__


def _parse_admin_ids(raw: str) -> frozenset[int]:
    # admin_ids=111,222 из env
    if not raw.strip():
        return frozenset()
    parts = [p.strip() for p in raw.split(",")]
    out: list[int] = []
    for p in parts:
        if not p:
            continue
        out.append(int(p))
    return frozenset(out)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    target_chat_id: int
    admin_ids: frozenset[int]
    sqlite_path: str
    app_version: str


@lru_cache
def get_settings() -> Settings:
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    chat_raw = os.environ.get("TARGET_CHAT_ID", "").strip()
    if not chat_raw:
        raise RuntimeError("TARGET_CHAT_ID is not set")
    target_chat_id = int(chat_raw)

    admins_raw = os.environ.get("ADMIN_IDS", "").strip()
    admin_ids = _parse_admin_ids(admins_raw)

    sqlite_path = os.environ.get("SQLITE_PATH", "data/quest_bot.db").strip() or "data/quest_bot.db"

    return Settings(
        bot_token=token,
        target_chat_id=target_chat_id,
        admin_ids=admin_ids,
        sqlite_path=sqlite_path,
        app_version=__version__,
    )


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()

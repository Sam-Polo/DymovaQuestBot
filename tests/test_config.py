import pytest

from quest_bot.config import Settings, _parse_admin_ids, get_settings


def test_parse_admin_ids():
    assert _parse_admin_ids("") == frozenset()
    assert _parse_admin_ids("1, 2 ,3") == frozenset([1, 2, 3])


def test_get_settings_requires_token(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("TARGET_CHAT_ID", raising=False)
    with pytest.raises(RuntimeError, match="BOT_TOKEN"):
        get_settings()


def test_get_settings_ok(monkeypatch, tmp_path):
    monkeypatch.setenv("BOT_TOKEN", "fake:token")
    monkeypatch.setenv("TARGET_CHAT_ID", "-100")
    monkeypatch.setenv("ADMIN_IDS", "10,20")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "db.sqlite"))
    s = get_settings()
    assert isinstance(s, Settings)
    assert s.target_chat_id == -100
    assert s.admin_ids == frozenset([10, 20])

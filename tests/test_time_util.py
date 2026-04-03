from datetime import datetime
from zoneinfo import ZoneInfo

from quest_bot.time_util import msk_date_str

_MSK = ZoneInfo("Europe/Moscow")


def test_msk_date_str_from_utc_evening_still_prev_calendar_day_msk():
    # 2026-04-02 22:00 UTC = 2026-04-03 01:00 MSK
    dt = datetime(2026, 4, 2, 22, 0, 0, tzinfo=ZoneInfo("UTC"))
    assert msk_date_str(dt) == "2026-04-03"


def test_msk_date_str_naive_treated_as_msk():
    dt = datetime(2026, 1, 15, 12, 0, 0)
    assert msk_date_str(dt) == "2026-01-15"

from unittest.mock import patch

from quest_bot.db import Database


@patch("quest_bot.db.msk_date_str", return_value="2026-04-03")
def test_daily_count_same_msk_day(_mock_msk, tmp_path):
    db = Database(str(tmp_path / "a.db"))
    db.init()
    db.upsert_user_start(1, "u", "n")
    assert db.count_questions_today_msk(1) == 0
    for i in range(3):
        db.insert_question_thread(
            psych_chat_id=-100,
            psych_message_id=200 + i,
            user_id=1,
            user_message_id=50 + i,
            question_text=f"q{i}",
        )
    assert db.count_questions_today_msk(1) == 3


def test_thread_roundtrip(tmp_path):
    db = Database(str(tmp_path / "b.db"))
    db.init()
    db.insert_question_thread(
        psych_chat_id=-100,
        psych_message_id=55,
        user_id=42,
        user_message_id=9,
        question_text="hi",
    )
    t = db.get_thread_by_psych_message(-100, 55)
    assert t is not None
    assert t.user_id == 42
    assert t.user_message_id == 9
    assert t.question_text == "hi"
    assert db.get_thread_by_psych_message(-100, 56) is None


def test_stats_and_users(tmp_path):
    db = Database(str(tmp_path / "c.db"))
    db.init()
    assert db.stats() == {
        "users": 0,
        "questions": 0,
        "answered": 0,
        "unanswered": 0,
    }
    db.upsert_user_start(5, None, "A")
    db.upsert_user_start(7, "u7", "B")
    st = db.stats()
    assert st["users"] == 2
    assert st["questions"] == 0
    assert st["answered"] == 0
    assert st["unanswered"] == 0
    rows = db.list_users_with_counts()
    assert len(rows) == 2
    by_id = {r.tg_user_id: r for r in rows}
    assert by_id[5].questions_total == 0
    assert by_id[7].questions_total == 0


def test_stats_answered_unanswered(tmp_path):
    db = Database(str(tmp_path / "e.db"))
    db.init()
    db.insert_question_thread(
        psych_chat_id=-100,
        psych_message_id=10,
        user_id=1,
        user_message_id=1,
        question_text="a",
    )
    db.insert_question_thread(
        psych_chat_id=-100,
        psych_message_id=11,
        user_id=1,
        user_message_id=2,
        question_text="b",
    )
    st = db.stats()
    assert st["questions"] == 2
    assert st["unanswered"] == 2
    assert st["answered"] == 0
    db.mark_thread_answered(-100, 10)
    st2 = db.stats()
    assert st2["answered"] == 1
    assert st2["unanswered"] == 1
    assert st2["questions"] == 2


def test_clear_all_question_threads(tmp_path):
    db = Database(str(tmp_path / "f.db"))
    db.init()
    db.insert_question_thread(
        psych_chat_id=-100,
        psych_message_id=1,
        user_id=1,
        user_message_id=1,
        question_text="x",
    )
    assert db.stats()["questions"] == 1
    n = db.clear_all_question_threads()
    assert n == 1
    assert db.stats()["questions"] == 0
    assert db.stats()["answered"] == 0
    assert db.stats()["unanswered"] == 0


def test_user_questions_total_after_inserts(tmp_path):
    db = Database(str(tmp_path / "d.db"))
    db.init()
    db.upsert_user_start(9, None, "X")
    db.insert_question_thread(
        psych_chat_id=-100,
        psych_message_id=1,
        user_id=9,
        user_message_id=2,
        question_text="one",
    )
    rows = db.list_users_with_counts()
    assert len(rows) == 1
    assert rows[0].questions_total == 1

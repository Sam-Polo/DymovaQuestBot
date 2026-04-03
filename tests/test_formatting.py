from quest_bot.formatting import (
    answer_for_user,
    format_question_for_psych,
    greeting_text,
    user_header_line,
)


def test_user_header_with_username():
    assert user_header_line("Anna", "anna") == "Пользователь: Anna @anna"


def test_user_header_no_username():
    line = user_header_line("Anna", None)
    assert "Anna" in line
    assert "Telegram" in line


def test_format_question_for_psych():
    t = format_question_for_psych("Ivan", "ivan", "How?")
    assert "Ivan" in t
    assert "@ivan" in t
    assert "How?" in t
    assert "💬" in t


def test_answer_for_user():
    t = answer_for_user("  да  ")
    assert "Ваш ответ на вопрос:" in t
    assert t.startswith("Ваш ответ на вопрос:\n\n")
    assert "да" in t


def test_greeting_nonempty():
    assert len(greeting_text()) > 40

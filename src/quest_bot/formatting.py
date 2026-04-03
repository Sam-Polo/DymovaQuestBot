def user_header_line(first_name: str | None, username: str | None) -> str:
    # строка для чата психолога: имя + ник или пометка что ника нет
    name = (first_name or "без имени").strip()
    if username:
        return f"Пользователь: {name} @{username}"
    return f"Пользователь: {name} (ник в Telegram отсутствует)"


def format_question_for_psych(first_name: str | None, username: str | None, question: str) -> str:
    head = user_header_line(first_name, username)
    return f"{head}\n\n💬{question}"


def answer_for_user(psychologist_text: str) -> str:
    body = psychologist_text.strip()
    # две пустые строки между заголовком и текстом ответа
    return f"Ваш ответ на вопрос:\n\n\n{body} ✅"


def greeting_text() -> str:
    return (
        "Привет! 👋 Здесь ты можешь задать вопрос полностью анонимно и получить ответ. "
        "Напиши свой вопрос одним сообщением — я передам его специалисту. 🌿"
    )


def need_start_text() -> str:
    return "Чтобы задать вопрос, сначала нажми /start 🌱"


def limit_reached_text() -> str:
    return "Сегодня можно задать не больше 3 вопросов (лимит по МСК). Попробуй завтра. ⏳"


def need_text_only() -> str:
    return "Пока принимаю только текстовые вопросы — напиши сообщением. ✏️"


def help_admin_text() -> str:
    return (
        "Команды (только для админов):\n"
        "/start — регистрация сценария / приветствие\n"
        "/stats — сводка: пользователи, вопросы, с ответом / без ответа\n"
        "/users — список пользователей с количеством вопросов\n"
        "/help — этот текст\n"
    )


def truncate_for_quote(text: str, max_len: int = 900) -> str:
    # ограничение чтобы не упереться в лимиты клиента/quote
    t = text.strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"

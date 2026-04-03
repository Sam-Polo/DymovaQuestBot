import logging

from telegram import BotCommand, Message, ReplyParameters, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes

from quest_bot.config import Settings
from quest_bot.db import Database
from quest_bot.formatting import (
    answer_for_user,
    format_question_for_psych,
    greeting_text,
    help_admin_text,
    limit_reached_text,
    need_start_text,
    need_text_only,
    truncate_for_quote,
)

log = logging.getLogger(__name__)


def _is_admin(user_id: int | None, settings: Settings) -> bool:
    if user_id is None:
        return False
    return user_id in settings.admin_ids


async def post_init_set_commands(application) -> None:
    await application.bot.set_my_commands(
        [BotCommand("start", "Начать и задать анонимный вопрос")],
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not _is_admin(update.effective_user.id if update.effective_user else None, settings):
        await update.effective_message.reply_text("Эта команда доступна только администраторам. 🔒")
        return
    await update.effective_message.reply_text(help_admin_text())


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not _is_admin(update.effective_user.id if update.effective_user else None, settings):
        await update.effective_message.reply_text("Эта команда доступна только администраторам. 🔒")
        return
    db: Database = context.application.bot_data["db"]
    st = db.stats()
    text = (
        f"Статистика 📊\n"
        f"Пользователей (нажимали /start): {st['users']}\n"
        f"Всего вопросов: {st['questions']}\n"
    )
    await update.effective_message.reply_text(text)


async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not _is_admin(update.effective_user.id if update.effective_user else None, settings):
        await update.effective_message.reply_text("Эта команда доступна только администраторам. 🔒")
        return
    db: Database = context.application.bot_data["db"]
    rows = db.list_users_with_counts()
    if not rows:
        await update.effective_message.reply_text("Пока нет пользователей. 👤")
        return
    lines: list[str] = ["Пользователи (были /start): 👥"]
    for r in rows:
        un = f"@{r.username}" if r.username else "нет ника"
        fn = (r.first_name or "—").strip()
        lines.append(f"· id={r.tg_user_id} | {fn} | {un} | вопросов: {r.questions_total}")
    text = "\n".join(lines)
    if len(text) > 3500:
        text = text[:3490] + "\n… (обрезано)"
    await update.effective_message.reply_text(text)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    db: Database = context.application.bot_data["db"]
    user = update.effective_user
    if user is None:
        return
    db.upsert_user_start(user.id, user.username, user.first_name)
    msg = update.effective_message
    # в группах тоже можно /start, но приветствие ориентировано на личку
    await msg.reply_text(greeting_text())


async def private_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    db: Database = context.application.bot_data["db"]
    msg = update.effective_message
    user = update.effective_user
    if msg is None or user is None:
        return
    if msg.chat.type != "private":
        return
    if not db.has_started(user.id):
        await msg.reply_text(need_start_text())
        return
    if not msg.text:
        await msg.reply_text(need_text_only())
        return
    q = msg.text.strip()
    if not q:
        await msg.reply_text(need_text_only())
        return
    used = db.count_questions_today_msk(user.id)
    if used >= 3:
        await msg.reply_text(limit_reached_text())
        return
    psych_text = format_question_for_psych(user.first_name, user.username, q)
    try:
        sent: Message = await context.bot.send_message(chat_id=settings.target_chat_id, text=psych_text)
    except TelegramError as e:
        log.warning("failed to send question to psych chat: %s", type(e).__name__)
        await msg.reply_text("Не удалось отправить вопрос. Попробуй позже. 🙏")
        return
    db.insert_question_thread(
        psych_chat_id=int(sent.chat_id),
        psych_message_id=int(sent.message_id),
        user_id=user.id,
        user_message_id=int(msg.message_id),
        question_text=q,
    )
    db.touch_user(user.id, user.username, user.first_name)
    await msg.reply_text("Вопрос отправлен. Ответ пришлю здесь, как только будет готов. 💬")


async def private_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db: Database = context.application.bot_data["db"]
    msg = update.effective_message
    user = update.effective_user
    if msg is None or user is None:
        return
    if msg.chat.type != "private":
        return
    if msg.text is not None:
        return
    if not db.has_started(user.id):
        await msg.reply_text(need_start_text())
        return
    await msg.reply_text(need_text_only())


async def psych_chat_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    db: Database = context.application.bot_data["db"]
    msg = update.effective_message
    chat = update.effective_chat
    if msg is None or chat is None:
        return
    if chat.id != settings.target_chat_id:
        return
    if msg.from_user and msg.from_user.id == context.bot.id:
        return
    if not msg.reply_to_message:
        return
    parent = msg.reply_to_message
    if parent.from_user is None or parent.from_user.id != context.bot.id:
        return
    thread = db.get_thread_by_psych_message(int(chat.id), int(parent.message_id))
    if thread is None:
        log.info("psych reply: unknown parent message_id=%s", parent.message_id)
        return
    answer_raw = (msg.text or msg.caption or "").strip()
    if not answer_raw:
        log.info("psych reply: empty text, skip")
        return
    text_user = answer_for_user(answer_raw)
    quote = truncate_for_quote(thread.question_text)
    try:
        await context.bot.send_message(
            chat_id=thread.user_id,
            text=text_user,
            reply_parameters=ReplyParameters(
                message_id=thread.user_message_id,
                chat_id=thread.user_id,
                quote=quote,
            ),
        )
    except BadRequest as e:
        log.info("send with quote failed (%s), retry reply only", type(e).__name__)
        try:
            await context.bot.send_message(
                chat_id=thread.user_id,
                text=text_user,
                reply_parameters=ReplyParameters(
                    message_id=thread.user_message_id,
                    chat_id=thread.user_id,
                ),
            )
        except TelegramError as e2:
            log.warning("failed to deliver answer to user: %s", type(e2).__name__)
    except TelegramError as e:
        log.warning("failed to deliver answer to user: %s", type(e).__name__)

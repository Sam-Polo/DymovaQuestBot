import logging

from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from quest_bot.config import get_settings
from quest_bot.db import Database
from quest_bot.handlers import (
    cmd_clear_stats,
    cmd_help,
    cmd_start,
    cmd_stats,
    cmd_users,
    post_init_set_commands,
    private_non_text,
    private_text_question,
    psych_chat_reply,
)
from quest_bot.log_setup import setup_logging

log = logging.getLogger(__name__)


async def _log_app_error(_update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.error:
        log.error("telegram handler error", exc_info=context.error)


def main() -> None:
    settings = get_settings()
    setup_logging(settings.app_version)

    db = Database(settings.sqlite_path)
    db.init()
    log.info("database ready")

    application = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(post_init_set_commands)
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["db"] = db
    application.bot_data["psych_chat_id"] = settings.target_chat_id

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("users", cmd_users))
    application.add_handler(CommandHandler("clear_stats", cmd_clear_stats))

    # не привязываемся к filters.Chat(chat_id=...): после миграции в супергруппу id меняется
    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS & filters.REPLY, psych_chat_reply),
    )
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            private_text_question,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & (~filters.TEXT) & ~filters.COMMAND,
            private_non_text,
        )
    )
    application.add_error_handler(_log_app_error)

    log.info("starting polling")
    application.run_polling(drop_pending_updates=True)

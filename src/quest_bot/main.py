import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from quest_bot.config import get_settings
from quest_bot.db import Database
from quest_bot.handlers import (
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

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("users", cmd_users))

    application.add_handler(
        MessageHandler(
            filters.Chat(chat_id=settings.target_chat_id) & filters.REPLY,
            psych_chat_reply,
        )
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

    log.info("starting polling")
    application.run_polling(drop_pending_updates=True)

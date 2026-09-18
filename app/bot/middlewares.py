import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import settings

logger = logging.getLogger(__name__)


def whitelist_only(handler_func):
    """
    Decorator to restrict bot access to whitelisted Telegram User IDs.
    """
    @wraps(handler_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat
        if not user:
            return

        allowed_ids = settings.allowed_user_ids
        is_allowed = not allowed_ids or (user.id in allowed_ids) or (chat and chat.id in allowed_ids)
        if not is_allowed:
            logger.warning(f"Unauthorized access attempt by user {user.id} (@{user.username}) in chat {chat.id if chat else 'None'}")
            if update.message:
                await update.message.reply_text(
                    f"⛔ **Akses Ditolak**\n\n"
                    f"User ID Anda (`{user.id}`) atau Chat ID ini (`{chat.id if chat else '-'}`) belum terdaftar pada daftar izin (`ALLOWED_TELEGRAM_USER_IDS`).\n"
                    f"Silakan hubungi Super Admin untuk menambahkan ID ini ke konfigurasi bot.",
                    parse_mode="Markdown",
                )
            elif update.callback_query:
                await update.callback_query.answer("⛔ Anda tidak memiliki akses ke bot ini.", show_alert=True)
            return

        return await handler_func(update, context, *args, **kwargs)

    return wrapper

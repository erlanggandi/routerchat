import logging
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config.settings import settings
from app.bot.handlers.command_handlers import (
    start_command,
    help_command,
    routers_command,
    use_command,
    addrouter_command,
    delrouter_command,
    status_command,
    traffic_command,
    interfaces_command,
    dhcp_command,
    firewall_command,
    logs_command,
    audit_command,
)
from app.bot.handlers.callback_handlers import handle_callback_query
from app.bot.handlers.chat_handlers import handle_chat_message

logger = logging.getLogger(__name__)


def create_bot_application() -> Application:
    """Builds and configures python-telegram-bot Application."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN belum diset di .env!")

    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("routers", routers_command))
    app.add_handler(CommandHandler("use", use_command))
    app.add_handler(CommandHandler("addrouter", addrouter_command))
    app.add_handler(CommandHandler("delrouter", delrouter_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("traffic", traffic_command))
    app.add_handler(CommandHandler("interfaces", interfaces_command))
    app.add_handler(CommandHandler("dhcp", dhcp_command))
    app.add_handler(CommandHandler("firewall", firewall_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("audit", audit_command))

    # Register Callback Query Handler (Inline Buttons for Approval & Router Select)
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Register Chat Message Handler (AI Natural Language)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message))

    return app

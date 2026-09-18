import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from app.database.connection import init_db
from app.bot.bot import create_bot_application
from app.api.v1.router import api_v1_router

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
)
logger = logging.getLogger(__name__)

bot_app = None
bot_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    logger.info("Initializing database...")
    await init_db()

    # Start Telegram Bot Polling if enabled and token is provided
    global bot_app, bot_task
    if (
        settings.ENABLE_TELEGRAM_POLLING
        and settings.TELEGRAM_BOT_TOKEN
        and settings.TELEGRAM_BOT_TOKEN != "your_telegram_bot_token_here"
    ):
        try:
            logger.info("Starting Telegram Bot Polling...")
            bot_app = create_bot_application()
            await bot_app.initialize()
            await bot_app.start()
            bot_task = asyncio.create_task(bot_app.updater.start_polling())
            logger.info("Telegram Bot polling started successfully!")
        except Exception as e:
            logger.error(f"Failed to start Telegram Bot polling: {e}")
    else:
        logger.info("Telegram Bot Polling is disabled or idle (REST API mode active).")

    yield

    # Shutdown:
    logger.info("Shutting down application...")
    if bot_app:
        try:
            if bot_app.updater and bot_app.updater.running:
                await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
        except Exception as e:
            logger.error(f"Error during Telegram bot shutdown: {e}")


app = FastAPI(
    title="AI MikroTik Service & Telegram Bot API",
    description="REST API & Webhook Service untuk integrasi asisten bot (Hermes) dan manajemen MikroTik RouterOS.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for external agents/frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1
app.include_router(api_v1_router)


@app.get("/")
async def root():
    return {
        "app": "AI MikroTik Service API",
        "status": "running",
        "version": "1.0.0",
        "telegram_polling": settings.ENABLE_TELEGRAM_POLLING,
        "docs": "/docs",
        "ai_provider": settings.AI_BASE_URL,
        "ai_model": settings.AI_MODEL,
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


def run():
    """CLI runner for local execution."""
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)


if __name__ == "__main__":
    run()

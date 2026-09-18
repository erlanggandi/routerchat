from fastapi import APIRouter, HTTPException
from app.schemas.api_schemas import NotifyMessageSchema
from app.utils.telegram_notifier import telegram_notifier

router = APIRouter(prefix="/telegram", tags=["Telegram Notification"])


@router.post("/notify")
async def send_telegram_notification(payload: NotifyMessageSchema):
    """Send a custom message or alert to the configured Telegram group/chat."""
    success = await telegram_notifier.send_message(
        text=payload.text,
        chat_id=payload.chat_id,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message to Telegram.")
    return {"status": "success", "message": "Notification delivered"}

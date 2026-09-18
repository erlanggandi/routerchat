import logging
import json
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.middlewares import whitelist_only
from app.database.connection import AsyncSessionLocal
from app.database import crud
from app.mikrotik.manager import router_manager
from app.ai.agent import ai_agent
from config.settings import settings

logger = logging.getLogger(__name__)


@whitelist_only
async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes natural language user requests using AI Agent with RouterOS context."""
    user = update.effective_user
    raw_text = update.message.text.strip() if update.message and update.message.text else ""

    if not raw_text:
        return

    # Clean bot username mention if mentioned in group
    bot_username = context.bot.username or "mikrotikassistBot"
    chat_text = re.sub(rf"@{bot_username}\b", "", raw_text, flags=re.IGNORECASE).strip()

    if not chat_text:
        await update.message.reply_text("👋 Halo! Ada yang bisa saya bantu terkait monitoring atau konfigurasi MikroTik?")
        return

    # Quick friendly greeting check
    lower_text = chat_text.lower()
    if lower_text in ["halo", "hai", "hello", "hi", "selamat pagi", "selamat siang", "selamat malam", "ping"]:
        await update.message.reply_text(
            f"👋 Halo, **{user.first_name}**!\n\n"
            f"Saya adalah asisten AI MikroTik Anda. Anda bisa bertanya dalam bahasa santai seperti:\n"
            f"• _\"Berapa persen beban CPU router sekarang?\"_\n"
            f"• _\"Tolong cek interface apa saja yang sedang down\"_\n"
            f"• _\"Cek perangkat apa saja di DHCP leases\"_\n\n"
            f"Atau gunakan perintah cepat seperti `/status`, `/traffic ether1`, dan `/routers`.",
            parse_mode="Markdown",
        )
        return

    await update.message.chat.send_action(action="typing")

    async with AsyncSessionLocal() as db:
        router, service = await router_manager.get_active_service_for_user(db, user.id)

        if not router or not service:
            all_routers = await crud.get_all_routers(db, active_only=True)
            if not all_routers:
                await update.message.reply_text(
                    "⚠️ **Belum ada router yang terdaftar.**\n\n"
                    "Sebelum mengobrol seputar jaringan, silakan daftarkan router pertama Anda dengan perintah:\n"
                    "`/addrouter <nama> <ip_host> <port> <username> <password>`\n\n"
                    "Contoh:\n`/addrouter kantor 192.168.88.1 8728 admin rahasia123`",
                    parse_mode="Markdown",
                )
                return
            else:
                # Ask user to choose one
                keyboard = [
                    [InlineKeyboardButton(f"🌐 {r.name} ({r.host})", callback_data=f"select_router:{r.id}")]
                    for r in all_routers
                ]
                await update.message.reply_text(
                    "📍 Silakan pilih router aktif yang ingin Anda kelola terlebih dahulu:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
                return

        # Check if AI Key is configured
        if not settings.AI_API_KEY or settings.AI_API_KEY == "your_openai_or_compatible_api_key_here":
            await update.message.reply_text(
                f"ℹ️ **Mode Chat AI Memerlukan API Key**\n\n"
                f"`AI_API_KEY` belum diisi di file `.env`.\n\n"
                f"Tetapi Anda tetap bisa menggunakan perintah cepat langsung ke router **{router.name}**:\n"
                f"• `/status` - Cek beban CPU, RAM & grafik\n"
                f"• `/traffic ether1` - Cek bandwidth grafik\n"
                f"• `/interfaces` - Cek daftar port\n"
                f"• `/dhcp` - Cek perangkat terhubung\n"
                f"• `/firewall` - Cek aturan firewall\n"
                f"• `/logs` - Cek log sistem",
                parse_mode="Markdown",
            )
            return

        # Run AI Agent
        reply_text, pending_proposals = await ai_agent.run(
            user_message=chat_text,
            service=service,
            db=db,
            user_id=user.id,
            router=router,
        )

        # Send AI response text
        try:
            await update.message.reply_text(reply_text, parse_mode="Markdown")
        except Exception:
            # Fallback to plain text if markdown formatting has unmatched tags
            await update.message.reply_text(reply_text)

        # If AI proposed configuration changes, render Approval cards
        for proposal in pending_proposals:
            approval_id = proposal["approval_id"]
            cmd_type = proposal["command_type"]
            path_str = "/".join(proposal["path_parts"])
            params_str = json.dumps(proposal["parameters"], indent=2)

            approval_msg = (
                f"🛡️ **Konfirmasi Perubahan Konfigurasi (Human-in-the-Loop)**\n\n"
                f"• **Router:** `{proposal['router_name']}`\n"
                f"• **Tindakan:** `{cmd_type}` pada `/{path_str}`\n"
                f"• **Keterangan:** {proposal['description']}\n\n"
                f"**Rincian Parameter:**\n"
                f"```json\n{params_str}\n```\n"
                f"⚠️ *Perubahan ini HANYA akan dieksekusi jika Anda menekan tombol Setujui di bawah.*"
            )

            keyboard = [
                [
                    InlineKeyboardButton("✅ Setujui & Terapkan", callback_data=f"approve:{approval_id}"),
                    InlineKeyboardButton("❌ Tolak", callback_data=f"reject:{approval_id}"),
                ]
            ]

            await update.message.reply_text(
                approval_msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

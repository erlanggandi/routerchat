import logging
import json
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from app.bot.middlewares import whitelist_only
from app.database.connection import AsyncSessionLocal
from app.database import crud
from app.mikrotik.manager import router_manager

logger = logging.getLogger(__name__)


@whitelist_only
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    user = update.effective_user

    async with AsyncSessionLocal() as db:
        # 1. Switch Router Selection
        if data.startswith("select_router:"):
            router_id_str = data.replace("select_router:", "")
            if not router_id_str.isdigit():
                await query.edit_message_text("⚠️ Router ID tidak valid.")
                return

            router_id = int(router_id_str)
            router = await crud.get_router_by_id(db, router_id)
            if not router:
                await query.edit_message_text("❌ Router tidak ditemukan.")
                return

            await crud.set_user_active_router(db, user.id, router_id)
            await query.edit_message_text(
                f"✅ **Router Aktif Diubah**\n\n"
                f"Sekarang Anda mengelola: **{router.name}** (`{router.host}:{router.port}`)\n"
                f"Gunakan `/status` atau chat langsung untuk memonitor.",
                parse_mode="Markdown",
            )
            return

        # 2. Approve Action
        if data.startswith("approve:"):
            approval_id = data.replace("approve:", "")
            approval = await crud.get_action_approval(db, approval_id)

            if not approval:
                await query.edit_message_text("❌ Data permohonan persetujuan tidak ditemukan.")
                return

            if approval.status != "PENDING":
                await query.edit_message_text(
                    f"ℹ️ Permohonan ini sudah diproses sebelumnya dengan status: **{approval.status}**",
                    parse_mode="Markdown",
                )
                return

            # Check expiry
            now_utc = datetime.now(timezone.utc)
            # Ensure timezone awareness match if approval.expires_at is naive
            expires_at = approval.expires_at if approval.expires_at.tzinfo else approval.expires_at.replace(tzinfo=timezone.utc)
            if now_utc > expires_at:
                await crud.update_action_approval_status(db, approval_id, "EXPIRED")
                await query.edit_message_text(
                    "⏱️ **Permohonan Kedaluwarsa (Expired)**\n\n"
                    "Batas waktu persetujuan telah habis. Silakan ajukan kembali jika masih dibutuhkan.",
                    parse_mode="Markdown",
                )
                return

            # Execute command
            router = await crud.get_router_by_id(db, approval.router_id)
            if not router:
                await query.edit_message_text("❌ Router target tidak ditemukan.")
                return

            try:
                payload = json.loads(approval.payload)
                path_parts = payload.get("path_parts", [])
                command_type = payload.get("command_type", "")
                params = payload.get("parameters", {})

                service = router_manager.get_service_for_router(router)
                exec_result = await service.execute_raw_command(path_parts, command_type, **params)
                result_str = str(exec_result) if exec_result is not None else "Sukses dieksekusi tanpa error."

                # Update approval & log
                await crud.update_action_approval_status(db, approval_id, "APPROVED", output=result_str)
                await crud.add_audit_log(
                    db,
                    user_id=user.id,
                    action_type="CONFIG_EXECUTE",
                    summary=f"Admin @{user.username or user.id} menyetujui perintah pada '{router.name}'",
                    details=f"Command: {command_type} {'/'.join(path_parts)}\nParams: {json.dumps(params)}\nResult: {result_str}",
                    router_id=router.id,
                )

                await query.edit_message_text(
                    f"✅ **Konfigurasi Berhasil Diterapkan!**\n\n"
                    f"• **Router:** `{router.name}`\n"
                    f"• **Deskripsi:** {approval.description}\n"
                    f"• **Perintah:** `{command_type}` pada `/{'/'.join(path_parts)}`\n"
                    f"• **Disetujui oleh:** @{user.username or user.first_name} (`{user.id}`)\n"
                    f"• **Waktu:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                    f"```text\n{result_str}\n```",
                    parse_mode="Markdown",
                )
            except Exception as exc:
                err_msg = str(exc)
                logger.error(f"Gagal mengeksekusi konfigurasi ke router: {err_msg}")
                await crud.update_action_approval_status(db, approval_id, "FAILED", output=err_msg)
                await crud.add_audit_log(
                    db,
                    user_id=user.id,
                    action_type="ERROR",
                    summary=f"Gagal mengeksekusi perintah pada '{router.name}'",
                    details=f"Error: {err_msg}",
                    router_id=router.id,
                )

                await query.edit_message_text(
                    f"❌ **Gagal Menerapkan Konfigurasi**\n\n"
                    f"• **Router:** `{router.name}`\n"
                    f"• **Error:** `{err_msg}`\n\n"
                    f"Pastikan hak akses pengguna MikroTik mengizinkan perintah ini.",
                    parse_mode="Markdown",
                )
            return

        # 3. Reject Action
        if data.startswith("reject:"):
            approval_id = data.replace("reject:", "")
            approval = await crud.get_action_approval(db, approval_id)

            if not approval:
                await query.edit_message_text("❌ Permohonan tidak ditemukan.")
                return

            if approval.status != "PENDING":
                await query.edit_message_text(
                    f"ℹ️ Permohonan ini sudah berstatus: **{approval.status}**",
                    parse_mode="Markdown",
                )
                return

            await crud.update_action_approval_status(db, approval_id, "REJECTED")
            await crud.add_audit_log(
                db,
                user_id=user.id,
                action_type="REJECT",
                summary=f"Admin @{user.username or user.id} menolak pengajuan konfigurasi",
                details=f"Deskripsi: {approval.description}",
                router_id=approval.router_id,
            )

            await query.edit_message_text(
                f"❌ **Pengajuan Ditolak**\n\n"
                f"• **Deskripsi:** {approval.description}\n"
                f"• **Ditolak oleh:** @{user.username or user.first_name} (`{user.id}`)\n"
                f"• **Status:** Dibatalkan. Tidak ada perubahan yang dilakukan pada router.",
                parse_mode="Markdown",
            )
            return

import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.middlewares import whitelist_only
from app.database.connection import AsyncSessionLocal
from app.database import crud
from app.mikrotik.manager import router_manager
from app.utils.grapher import generate_resource_chart, generate_traffic_chart

logger = logging.getLogger(__name__)


@whitelist_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as db:
        active_router = await crud.get_active_router_for_user(db, user.id)
        router_status = f"**{active_router.name}** (`{active_router.host}`)" if active_router else "_Belum ada yang dipilih_"

    welcome_text = (
        f"👋 Halo, **{user.first_name}**!\n\n"
        f"Selamat datang di **AI MikroTik Assistant Bot**.\n"
        f"Saya siap membantu Anda memantau dan mengelola router MikroTik secara remote dengan aman.\n\n"
        f"🌐 **Router Aktif Saat Ini:** {router_status}\n\n"
        f"📌 **Perintah Cepat:**\n"
        f"• `/status` - Cek beban CPU, RAM, & info sistem (+ grafik)\n"
        f"• `/traffic <interface>` - Cek grafik & kecepatan trafik (misal: `/traffic ether1`)\n"
        f"• `/interfaces` - Daftar interface & status koneksi\n"
        f"• `/dhcp` - Daftar perangkat terhubung (DHCP Leases)\n"
        f"• `/firewall` - Daftar aturan firewall filter\n"
        f"• `/logs` - Melihat log sistem terbaru\n"
        f"• `/routers` - Kelola & ganti router aktif\n"
        f"• `/help` - Panduan lengkap & contoh percakapan AI\n\n"
        f"💡 *Anda juga bisa langsung chat dengan bahasa santai, contoh: 'Berapa persen penggunaan CPU sekarang?' atau 'Blokir IP 192.168.1.50'.*"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


@whitelist_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"📖 **Panduan Penggunaan AI MikroTik Bot**\n\n"
        f"**1. Perintah Monitoring:**\n"
        f"• `/status` : Status performa router (CPU, RAM, Uptime) & grafik.\n"
        f"• `/traffic <interface>` : Monitor bandwidth interface secara real-time.\n"
        f"• `/interfaces` : Menampilkan semua interface jaringan.\n"
        f"• `/dhcp` : Melihat daftar DHCP Leases (IP, MAC, Hostname).\n"
        f"• `/firewall` : Melihat aturan firewall filter.\n"
        f"• `/logs` : Menampilkan 10 baris log router terbaru.\n"
        f"• `/audit` : Melihat riwayat persetujuan & aksi bot.\n\n"
        f"**2. Manajemen Multi-Router:**\n"
        f"• `/routers` : Menampilkan daftar router yang terdaftar.\n"
        f"• `/use <nama/id>` : Berganti router aktif untuk sesi Anda.\n"
        f"• `/addrouter <nama> <host> <port> <user> <pass>` : Mendaftarkan router baru.\n"
        f"• `/delrouter <id>` : Menghapus router dari sistem.\n\n"
        f"**3. Percakapan AI Cerdas:**\n"
        f"Anda bisa bertanya langsung dengan bahasa alami:\n"
        f"• _\"Cek apa ada IP yang aneh di DHCP?\"_\n"
        f"• _\"Tolong buatkan firewall filter untuk drop port 23 telnet.\"_\n"
        f"• _\"Analisa log sistem apakah ada percobaan brute-force.\"_\n\n"
        f"🛡️ **Sistem Keamanan (Human-in-the-loop):**\n"
        f"Setiap saran AI yang bersifat mengubah/menambah konfigurasi router HANYA akan dieksekusi setelah Anda menekan tombol **[ Setujui & Terapkan ]**."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


@whitelist_only
async def routers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as db:
        all_routers = await crud.get_all_routers(db, active_only=False)
        active_router = await crud.get_active_router_for_user(db, user.id)

        if not all_routers:
            await update.message.reply_text(
                "ℹ️ Belum ada router yang terdaftar di database.\n\n"
                "Gunakan perintah `/addrouter` untuk menambahkan router pertama.",
                parse_mode="Markdown",
            )
            return

        msg = "📋 **Daftar Router MikroTik Terdaftar:**\n\n"
        keyboard = []
        for r in all_routers:
            is_current = active_router and (active_router.id == r.id)
            tag = "✅ [AKTIF] " if is_current else "⚪ "
            msg += f"{tag}**ID {r.id}: {r.name}**\n   Host: `{r.host}:{r.port}` | SSL: `{r.use_ssl}`\n"
            keyboard.append([InlineKeyboardButton(f"{'✅ ' if is_current else ''}Pilih: {r.name}", callback_data=f"select_router:{r.id}")])

        msg += "\n*Klik tombol di bawah untuk berganti router aktif, atau ketik `/use <nama>`*"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


@whitelist_only
async def use_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("⚠️ Format salah. Gunakan: `/use <nama_router_atau_id>`", parse_mode="Markdown")
        return

    target = context.args[0].strip()
    async with AsyncSessionLocal() as db:
        if target.isdigit():
            router = await crud.get_router_by_id(db, int(target))
        else:
            router = await crud.get_router_by_name(db, target)

        if not router:
            await update.message.reply_text(f"❌ Router dengan nama/ID `{target}` tidak ditemukan.", parse_mode="Markdown")
            return

        await crud.set_user_active_router(db, user.id, router.id)
        await update.message.reply_text(
            f"✅ **Router Aktif Dialihkan!**\n\n"
            f"Anda sekarang mengelola router: **{router.name}** (`{router.host}:{router.port}`)",
            parse_mode="Markdown",
        )


@whitelist_only
async def addrouter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Format: /addrouter <name> <host> <port> <username> <password> [use_ssl]
    args = context.args
    if not args or len(args) < 5:
        await update.message.reply_text(
            "⚠️ Format perintah belum lengkap.\n\n"
            "**Format:**\n`/addrouter <nama> <host> <port> <username> <password> [ssl:true/false]`\n\n"
            "**Contoh:**\n`/addrouter kantor-pusat 192.168.88.1 8728 admin Rahasia123 false`",
            parse_mode="Markdown",
        )
        return

    name, host, port_str, username, password = args[0], args[1], args[2], args[3], args[4]
    port = int(port_str) if port_str.isdigit() else 8728
    use_ssl = (len(args) > 5 and args[5].lower() in ["true", "1", "yes", "ssl"])

    user = update.effective_user
    async with AsyncSessionLocal() as db:
        existing = await crud.get_router_by_name(db, name)
        if existing:
            await update.message.reply_text(f"⚠️ Router dengan nama `{name}` sudah terdaftar.", parse_mode="Markdown")
            return

        router = await crud.create_router(
            db=db,
            name=name,
            host=host,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
        )

        # Set as active if user currently has none
        active = await crud.get_active_router_for_user(db, user.id)
        if not active:
            await crud.set_user_active_router(db, user.id, router.id)

        await crud.add_audit_log(
            db,
            user_id=user.id,
            action_type="CONFIG_EXECUTE",
            summary=f"Admin mendaftarkan router baru: {name}",
            router_id=router.id,
        )

        await update.message.reply_text(
            f"✅ **Router Berhasil Ditambahkan!**\n\n"
            f"• **Nama:** `{router.name}`\n"
            f"• **Host:** `{router.host}:{router.port}`\n"
            f"• **SSL:** `{router.use_ssl}`\n"
            f"• **Status:** Aktif\n\n"
            f"Gunakan `/status` untuk menguji koneksi.",
            parse_mode="Markdown",
        )


@whitelist_only
async def delrouter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("⚠️ Format salah. Gunakan: `/delrouter <id>`", parse_mode="Markdown")
        return

    router_id = int(args[0])
    async with AsyncSessionLocal() as db:
        router = await crud.get_router_by_id(db, router_id)
        if not router:
            await update.message.reply_text(f"❌ Router ID `{router_id}` tidak ditemukan.", parse_mode="Markdown")
            return

        router_name = router.name
        await crud.delete_router(db, router_id)
        await update.message.reply_text(f"🗑️ Router **{router_name}** (ID: {router_id}) berhasil dihapus.", parse_mode="Markdown")


@whitelist_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.chat.send_action(action="typing")

    async with AsyncSessionLocal() as db:
        router, service = await router_manager.get_active_service_for_user(db, user.id)
        if not router or not service:
            await update.message.reply_text("⚠️ Belum ada router aktif yang dipilih. Gunakan `/routers`.", parse_mode="Markdown")
            return

        try:
            data = await service.get_system_resource()
            msg = (
                f"📊 **Status Router: {router.name}**\n"
                f"────────────────────────\n"
                f"• **Board:** `{data.get('board_name')}`\n"
                f"• **Versi RouterOS:** `{data.get('version')}`\n"
                f"• **Uptime:** `{data.get('uptime')}`\n"
                f"• **Beban CPU:** `{data.get('cpu_load')}%` ({data.get('cpu_count')} Core, {data.get('cpu_frequency')} MHz)\n"
                f"• **Penggunaan RAM:** `{data.get('memory_usage_pct')}%`\n"
                f"  └ Terpakai: `{data.get('used_memory_mb')} MB` / Bebas: `{data.get('free_memory_mb')} MB`\n"
                f"────────────────────────"
            )

            # Generate visual chart
            chart_buf = generate_resource_chart(
                router_name=router.name,
                cpu_load=data.get("cpu_load", 0),
                mem_usage_pct=data.get("memory_usage_pct", 0.0),
                used_mem_mb=data.get("used_memory_mb", 0.0),
                free_mem_mb=data.get("free_memory_mb", 0.0),
            )

            await update.message.reply_photo(photo=chart_buf, caption=msg, parse_mode="Markdown")
        except Exception as exc:
            await update.message.reply_text(f"❌ Gagal mengambil status router `{router.name}`: {str(exc)}", parse_mode="Markdown")


@whitelist_only
async def traffic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    interface_name = context.args[0].strip() if context.args else "ether1"
    await update.message.chat.send_action(action="typing")

    async with AsyncSessionLocal() as db:
        router, service = await router_manager.get_active_service_for_user(db, user.id)
        if not router or not service:
            await update.message.reply_text("⚠️ Belum ada router aktif yang dipilih. Gunakan `/routers`.", parse_mode="Markdown")
            return

        try:
            data = await service.get_interface_traffic(interface_name)
            if not data:
                await update.message.reply_text(f"⚠️ Tidak ada data trafik untuk interface `{interface_name}`.", parse_mode="Markdown")
                return

            rx_mbps = data.get("rx_mbps", 0.0)
            tx_mbps = data.get("tx_mbps", 0.0)
            rx_pps = data.get("rx_packets", 0)
            tx_pps = data.get("tx_packets", 0)

            msg = (
                f"📈 **Trafik Real-time: {interface_name}** ({router.name})\n"
                f"────────────────────────\n"
                f"⬇️ **Download (RX):** `{rx_mbps} Mbps` ({rx_pps} pps)\n"
                f"⬆️ **Upload (TX):** `{tx_mbps} Mbps` ({tx_pps} pps)\n"
                f"────────────────────────"
            )

            chart_buf = generate_traffic_chart(
                interface_name=interface_name,
                rx_mbps=rx_mbps,
                tx_mbps=tx_mbps,
                rx_pps=rx_pps,
                tx_pps=tx_pps,
            )

            await update.message.reply_photo(photo=chart_buf, caption=msg, parse_mode="Markdown")
        except Exception as exc:
            await update.message.reply_text(f"❌ Gagal mengambil trafik interface `{interface_name}`: {str(exc)}", parse_mode="Markdown")


@whitelist_only
async def interfaces_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as db:
        router, service = await router_manager.get_active_service_for_user(db, user.id)
        if not router or not service:
            await update.message.reply_text("⚠️ Belum ada router aktif yang dipilih.", parse_mode="Markdown")
            return

        try:
            interfaces = await service.get_interfaces()
            msg = f"🔌 **Daftar Interface: {router.name}**\n\n"
            for iface in interfaces:
                status_icon = "🟢" if iface.get("running") else ("🔴" if iface.get("disabled") else "⚪")
                state = "Running" if iface.get("running") else ("Disabled" if iface.get("disabled") else "Link Down")
                comment = f" - _{iface.get('comment')}_" if iface.get("comment") else ""
                msg += f"{status_icon} **{iface.get('name')}** (`{iface.get('type')}`) : {state}{comment}\n"

            msg += "\n_Tip: Gunakan `/traffic <nama_interface>` untuk melihat grafik bandwidth._"
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as exc:
            await update.message.reply_text(f"❌ Gagal mengambil daftar interface: {str(exc)}", parse_mode="Markdown")


@whitelist_only
async def dhcp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as db:
        router, service = await router_manager.get_active_service_for_user(db, user.id)
        if not router or not service:
            await update.message.reply_text("⚠️ Belum ada router aktif yang dipilih.", parse_mode="Markdown")
            return

        try:
            leases = await service.get_dhcp_leases()
            if not leases:
                await update.message.reply_text(f"ℹ️ Tidak ada data DHCP Leases aktif di `{router.name}`.", parse_mode="Markdown")
                return

            msg = f"📱 **DHCP Leases ({router.name}) - Total {len(leases)}:**\n\n"
            for item in leases[:20]:  # Cap at 20 for readability
                msg += f"• `{item.get('address')}` | `{item.get('mac_address')}` | *{item.get('host_name')}*\n"

            if len(leases) > 20:
                msg += f"\n_...dan {len(leases) - 20} perangkat lainnya._"

            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as exc:
            await update.message.reply_text(f"❌ Gagal mengambil DHCP Leases: {str(exc)}", parse_mode="Markdown")


@whitelist_only
async def firewall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as db:
        router, service = await router_manager.get_active_service_for_user(db, user.id)
        if not router or not service:
            await update.message.reply_text("⚠️ Belum ada router aktif yang dipilih.", parse_mode="Markdown")
            return

        try:
            rules = await service.get_firewall_filters()
            if not rules:
                await update.message.reply_text(f"ℹ️ Belum ada aturan firewall filter di `{router.name}`.", parse_mode="Markdown")
                return

            msg = f"🛡️ **Firewall Filter Rules ({router.name}) - Total {len(rules)}:**\n\n"
            for idx, r in enumerate(rules[:15]):
                state = "❌ Disabled" if r.get("disabled") else "✅ Active"
                msg += f"**#{idx+1} [{r.get('chain').upper()}]** -> `{r.get('action')}` ({state})\n"
                msg += f"   Src: `{r.get('src_address')}` | Dst: `{r.get('dst_address')}` | Proto: `{r.get('protocol')}`\n"
                if r.get("comment"):
                    msg += f"   _Keterangan: {r.get('comment')}_\n"

            if len(rules) > 15:
                msg += f"\n_...dan {len(rules) - 15} aturan lainnya._"

            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as exc:
            await update.message.reply_text(f"❌ Gagal mengambil aturan firewall: {str(exc)}", parse_mode="Markdown")


@whitelist_only
async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as db:
        router, service = await router_manager.get_active_service_for_user(db, user.id)
        if not router or not service:
            await update.message.reply_text("⚠️ Belum ada router aktif yang dipilih.", parse_mode="Markdown")
            return

        try:
            logs = await service.get_system_logs(limit=10)
            if not logs:
                await update.message.reply_text("ℹ️ Log router kosong.", parse_mode="Markdown")
                return

            msg = f"📜 **Log Sistem Terbaru ({router.name}):**\n\n"
            for log_entry in logs:
                msg += f"• `[{log_entry.get('time')}]` *{log_entry.get('topics')}*: {log_entry.get('message')}\n"

            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as exc:
            await update.message.reply_text(f"❌ Gagal mengambil log router: {str(exc)}", parse_mode="Markdown")


@whitelist_only
async def audit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with AsyncSessionLocal() as db:
        logs = await crud.get_recent_audit_logs(db, limit=10)
        if not logs:
            await update.message.reply_text("ℹ️ Belum ada riwayat audit log.", parse_mode="Markdown")
            return

        msg = "📑 **Riwayat Audit Log Terbaru (10 Terakhir):**\n\n"
        for l in logs:
            action_tag = f"[{l.action_type}]"
            time_str = l.created_at.strftime("%Y-%m-%d %H:%M")
            msg += f"• `{time_str}` **{action_tag}**: {l.summary}\n"

        await update.message.reply_text(msg, parse_mode="Markdown")

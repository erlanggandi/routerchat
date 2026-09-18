import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession
from app.mikrotik.service import MikrotikService
from app.database.models import Router
from app.database import crud


def build_tools(
    service: MikrotikService,
    db: AsyncSession,
    user_id: int,
    router: Router,
) -> tuple[List[Any], List[Dict[str, Any]]]:
    """
    Constructs LangChain tools bound to the active router and user context.
    Returns (tools_list, pending_proposals_collector).
    """
    pending_proposals: List[Dict[str, Any]] = []

    @tool
    async def get_system_resource() -> str:
        """Mendapatkan data status performa router saat ini: CPU load, RAM total/used/free, uptime, board name, dan versi RouterOS."""
        try:
            data = await service.get_system_resource()
            await crud.add_audit_log(
                db,
                user_id=user_id,
                action_type="QUERY",
                summary=f"Cek system resource pada router '{router.name}'",
                router_id=router.id,
            )
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error mengambil system resource: {str(e)}"

    @tool
    async def get_interfaces() -> str:
        """Mendapatkan daftar interface jaringan di router beserta status running (aktif terhubung) dan disabled."""
        try:
            data = await service.get_interfaces()
            await crud.add_audit_log(
                db,
                user_id=user_id,
                action_type="QUERY",
                summary=f"Cek interface list pada router '{router.name}'",
                router_id=router.id,
            )
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error mengambil data interfaces: {str(e)}"

    @tool
    async def get_interface_traffic(interface_name: str) -> str:
        """Mengambil kecepatan trafik real-time (RX/TX Mbps dan Packets per second) pada interface tertentu (contoh: 'ether1', 'wlan1')."""
        try:
            data = await service.get_interface_traffic(interface_name.strip())
            await crud.add_audit_log(
                db,
                user_id=user_id,
                action_type="QUERY",
                summary=f"Cek traffic {interface_name} pada router '{router.name}'",
                router_id=router.id,
            )
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error mengambil traffic {interface_name}: {str(e)}"

    @tool
    async def get_dhcp_leases() -> str:
        """Mendapatkan daftar perangkat (IP address, MAC address, Hostname) yang terhubung via DHCP Server di router."""
        try:
            data = await service.get_dhcp_leases()
            await crud.add_audit_log(
                db,
                user_id=user_id,
                action_type="QUERY",
                summary=f"Cek DHCP leases pada router '{router.name}'",
                router_id=router.id,
            )
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error mengambil data DHCP leases: {str(e)}"

    @tool
    async def get_firewall_filters() -> str:
        """Mendapatkan daftar aturan firewall filter (/ip firewall filter) yang sedang aktif di router."""
        try:
            data = await service.get_firewall_filters()
            await crud.add_audit_log(
                db,
                user_id=user_id,
                action_type="QUERY",
                summary=f"Cek firewall filters pada router '{router.name}'",
                router_id=router.id,
            )
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error mengambil aturan firewall: {str(e)}"

    @tool
    async def get_system_logs(limit: int = 10) -> str:
        """Melihat baris log sistem router terbaru untuk mendiagnosa error, login attempt, atau perubahan status."""
        try:
            data = await service.get_system_logs(limit=limit)
            await crud.add_audit_log(
                db,
                user_id=user_id,
                action_type="QUERY",
                summary=f"Cek system logs (limit {limit}) pada router '{router.name}'",
                router_id=router.id,
            )
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error mengambil log sistem: {str(e)}"

    @tool
    async def propose_router_config(
        command_type: str,
        description: str,
        path_parts: List[str],
        parameters: Dict[str, Any],
    ) -> str:
        """
        WAJIB DIGUNAKAN untuk setiap tindakan yang mengubah/menambah/menghapus konfigurasi router (WRITE / MUTATING).
        Tool ini TIDAK langsung mengeksekusi ke router, melainkan membuat proposal persetujuan manual (Approval Engine) untuk disetujui admin melalui tombol di Telegram.
        
        Args:
            command_type: Jenis perintah ('add', 'remove', 'set', 'enable', 'disable')
            description: Penjelasan tujuan dan dampak perubahan konfigurasi dalam Bahasa Indonesia
            path_parts: Hirarki API MikroTik, contoh: ["ip", "firewall", "filter"]
            parameters: Parameter konfigurasi MikroTik (contoh: {"chain": "forward", "src_address": "192.168.1.50", "action": "drop"})
        """
        try:
            payload = {
                "path_parts": path_parts,
                "command_type": command_type,
                "parameters": parameters,
            }
            approval = await crud.create_action_approval(
                db=db,
                user_id=user_id,
                router_id=router.id,
                command_type=command_type,
                description=description,
                payload=payload,
            )
            await crud.add_audit_log(
                db,
                user_id=user_id,
                action_type="APPROVAL_REQUEST",
                summary=f"Pengajuan konfigurasi ({command_type} {'/'.join(path_parts)}) pada router '{router.name}'",
                details=f"Deskripsi: {description}\nParameter: {json.dumps(parameters)}",
                router_id=router.id,
            )

            pending_proposals.append({
                "approval_id": approval.id,
                "description": description,
                "command_type": command_type,
                "path_parts": path_parts,
                "parameters": parameters,
                "router_name": router.name,
            })

            return (
                f"PROPOSAL DIBUAT DENGAN ID: {approval.id}. "
                f"Rincian: {description}. "
                f"Perintah menunggu persetujuan admin melalui tombol konfirmasi di Telegram."
            )
        except Exception as e:
            return f"Gagal membuat proposal konfigurasi: {str(e)}"

    @tool
    async def list_all_routers() -> str:
        """Melihat daftar semua router MikroTik yang terdaftar di sistem dan mengetahui router mana yang sedang aktif dipilih saat ini."""
        try:
            routers = await crud.get_all_routers(db, active_only=False)
            current_active = await crud.get_active_router_for_user(db, user_id)
            active_id = current_active.id if current_active else None

            output = []
            for r in routers:
                output.append({
                    "id": r.id,
                    "name": r.name,
                    "host": f"{r.host}:{r.port}",
                    "is_active_selection": (r.id == active_id),
                    "description": r.description or "-",
                })
            return json.dumps(output, indent=2)
        except Exception as e:
            return f"Error mengambil daftar router: {str(e)}"

    @tool
    async def add_new_router(
        name: str,
        host: str,
        username: str,
        password: str,
        port: int = 8728,
        use_ssl: bool = False,
        description: str = "",
    ) -> str:
        """Mendaftarkan perangkat router MikroTik baru ke dalam sistem agar bisa dikelola."""
        try:
            existing = await crud.get_router_by_name(db, name.strip())
            if existing:
                return f"Router dengan nama '{name}' sudah terdaftar sebelumnya (ID: {existing.id})."
            new_r = await crud.create_router(
                db=db,
                name=name.strip(),
                host=host.strip(),
                username=username.strip(),
                password=password.strip(),
                port=port,
                use_ssl=use_ssl,
                description=description or None,
            )
            return f"Sukses mendaftarkan router baru '{new_r.name}' (ID: {new_r.id}) pada host {new_r.host}:{new_r.port}."
        except Exception as e:
            return f"Gagal menambahkan router: {str(e)}"

    @tool
    async def switch_active_router(router_name_or_id: str) -> str:
        """Mengganti atau memilih router aktif yang ingin dikelola oleh pengguna (bisa menggunakan nama router atau ID router)."""
        try:
            target = router_name_or_id.strip()
            if target.isdigit():
                target_router = await crud.get_router_by_id(db, int(target))
            else:
                target_router = await crud.get_router_by_name(db, target)

            if not target_router:
                return f"Router '{target}' tidak ditemukan. Panggil tool list_all_routers untuk melihat nama router yang tersedia."

            await crud.set_user_active_router(db, user_id, target_router.id)
            return f"Berhasil mengalihkan sesi aktif! Sekarang Anda sedang mengelola router '{target_router.name}' ({target_router.host}:{target_router.port})."
        except Exception as e:
            return f"Gagal mengganti router aktif: {str(e)}"

    tools_list = [
        get_system_resource,
        get_interfaces,
        get_interface_traffic,
        get_dhcp_leases,
        get_firewall_filters,
        get_system_logs,
        propose_router_config,
        list_all_routers,
        add_new_router,
        switch_active_router,
    ]

    return tools_list, pending_proposals

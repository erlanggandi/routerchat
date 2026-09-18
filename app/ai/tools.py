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

    tools_list = [
        get_system_resource,
        get_interfaces,
        get_interface_traffic,
        get_dhcp_leases,
        get_firewall_filters,
        get_system_logs,
        propose_router_config,
    ]

    return tools_list, pending_proposals

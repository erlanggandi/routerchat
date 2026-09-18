"""
Hermes MikroTik Tool Integration
================================
File ini dapat disalin atau di-import langsung oleh bot Hermes Anda di Ubuntu (app@10.10.70.251)
untuk memanggil backend MikroTik AI via HTTP REST API.
"""

import os
import requests
from typing import Dict, Any, Optional

# Alamat backend MikroTik (http://10.10.70.251:3010 atau http://localhost:3010)
MIKROTIK_BACKEND_URL = os.getenv("MIKROTIK_BACKEND_URL", "http://10.10.70.251:3010")


def ask_mikrotik_ai(message: str, user_id: int = 1, router_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Kirim pertanyaan bahasa alami dari Hermes ke MikroTik AI Assistant.
    Contoh: "Berapa persen beban CPU saat ini?" atau "Blokir IP 192.168.88.50"
    """
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/chat"
    payload = {
        "message": message,
        "user_id": user_id,
        "router_id": router_id,
        "send_to_telegram": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=35)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"reply": f"Gagal menghubungi MikroTik AI: {str(e)}", "pending_approvals": []}


def get_router_resource(router_id: int = 1) -> Dict[str, Any]:
    """Mendapatkan data beban CPU, RAM, uptime, dan versi RouterOS."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/routers/{router_id}/monitoring/resource"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_router_traffic(interface: str = "ether1", router_id: int = 1) -> Dict[str, Any]:
    """Mendapatkan kecepatan trafik download/upload real-time pada interface tertentu."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/routers/{router_id}/monitoring/traffic"
    try:
        resp = requests.get(url, params={"interface": interface}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_router_interfaces(router_id: int = 1) -> Dict[str, Any]:
    """Mendapatkan daftar semua interface dan status link."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/routers/{router_id}/monitoring/interfaces"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_dhcp_leases(router_id: int = 1) -> Dict[str, Any]:
    """Mendapatkan daftar perangkat yang terhubung ke router via DHCP server."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/routers/{router_id}/monitoring/dhcp-leases"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def approve_action(approval_id: str, user_id: int = 1) -> Dict[str, Any]:
    """Menyetujui dan mengeksekusi perubahan konfigurasi jaringan MikroTik."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/approvals/{approval_id}/approve"
    try:
        resp = requests.post(url, json={"user_id": user_id}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def reject_action(approval_id: str, user_id: int = 1) -> Dict[str, Any]:
    """Menolak usulan perubahan konfigurasi jaringan."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/approvals/{approval_id}/reject"
    try:
        resp = requests.post(url, json={"user_id": user_id}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ---------------- Multi-Router Management ----------------

def list_routers(active_only: bool = True) -> Any:
    """Mendapatkan daftar semua router yang terdaftar."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/routers"
    try:
        resp = requests.get(url, params={"active_only": active_only}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def add_router(
    name: str,
    host: str,
    username: str,
    password: str,
    port: int = 8728,
    use_ssl: bool = False,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Mendaftarkan router baru ke sistem."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/routers"
    payload = {
        "name": name,
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "use_ssl": use_ssl,
        "description": description,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def select_active_router(user_id: int, router_id: int) -> Dict[str, Any]:
    """Memilih atau berganti router aktif untuk sesi pengguna."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/routers/select"
    try:
        resp = requests.post(url, json={"user_id": user_id, "router_id": router_id}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_active_router(user_id: int) -> Dict[str, Any]:
    """Mengecek router mana yang sedang aktif dikelola oleh pengguna."""
    url = f"{MIKROTIK_BACKEND_URL}/api/v1/routers/active"
    try:
        resp = requests.get(url, params={"user_id": user_id}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

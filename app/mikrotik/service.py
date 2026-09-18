import logging
import asyncio
from typing import Dict, Any, List, Optional
from app.mikrotik.client import MikrotikClient

logger = logging.getLogger(__name__)


class MikrotikService:
    def __init__(self, client: MikrotikClient):
        self.client = client

    def get_system_resource_sync(self) -> Dict[str, Any]:
        """Fetch router system resource information (CPU, RAM, Uptime, Board Name)."""
        with self.client:
            path = self.client.api.path("system", "resource")
            records = tuple(path())
            if not records:
                return {}
            res = records[0]

            # Parse memory in MB
            total_mem = int(res.get("total-memory", 0)) / (1024 * 1024)
            free_mem = int(res.get("free-memory", 0)) / (1024 * 1024)
            used_mem = total_mem - free_mem
            mem_usage_pct = (used_mem / total_mem * 100) if total_mem > 0 else 0

            return {
                "uptime": res.get("uptime", "N/A"),
                "version": res.get("version", "N/A"),
                "board_name": res.get("board-name", "Router"),
                "architecture_name": res.get("architecture-name", "N/A"),
                "cpu": res.get("cpu", "N/A"),
                "cpu_count": res.get("cpu-count", 1),
                "cpu_frequency": res.get("cpu-frequency", 0),
                "cpu_load": res.get("cpu-load", 0),
                "total_memory_mb": round(total_mem, 1),
                "free_memory_mb": round(free_mem, 1),
                "used_memory_mb": round(used_mem, 1),
                "memory_usage_pct": round(mem_usage_pct, 1),
            }

    async def get_system_resource(self) -> Dict[str, Any]:
        return await asyncio.to_thread(self.get_system_resource_sync)

    def get_interfaces_sync(self) -> List[Dict[str, Any]]:
        """Fetch list of interfaces and their status."""
        with self.client:
            path = self.client.api.path("interface")
            records = list(path())
            results = []
            for item in records:
                results.append({
                    "id": item.get(".id"),
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "running": item.get("running", False),
                    "disabled": item.get("disabled", False),
                    "comment": item.get("comment", ""),
                })
            return results

    async def get_interfaces(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_interfaces_sync)

    def get_interface_traffic_sync(self, interface_name: str) -> Dict[str, Any]:
        """Monitor live traffic rate on a specific interface."""
        with self.client:
            path = self.client.api.path("interface")
            # monitor-traffic interface=ether1 once=yes
            records = list(path.custom("monitor-traffic", interface=interface_name, once=True)())
            if not records:
                return {}
            data = records[0]

            rx_bps = int(data.get("rx-bits-per-second", 0))
            tx_bps = int(data.get("tx-bits-per-second", 0))

            return {
                "interface": interface_name,
                "rx_bps": rx_bps,
                "tx_bps": tx_bps,
                "rx_mbps": round(rx_bps / 1_000_000, 2),
                "tx_mbps": round(tx_bps / 1_000_000, 2),
                "rx_packets": int(data.get("rx-packets-per-second", 0)),
                "tx_packets": int(data.get("tx-packets-per-second", 0)),
            }

    async def get_interface_traffic(self, interface_name: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self.get_interface_traffic_sync, interface_name)

    def get_dhcp_leases_sync(self) -> List[Dict[str, Any]]:
        """Fetch DHCP server leases."""
        with self.client:
            path = self.client.api.path("ip", "dhcp-server", "lease")
            records = list(path())
            leases = []
            for item in records:
                leases.append({
                    "address": item.get("address"),
                    "mac_address": item.get("mac-address"),
                    "host_name": item.get("host-name", "-"),
                    "status": item.get("status", "-"),
                    "comment": item.get("comment", ""),
                    "disabled": item.get("disabled", False),
                })
            return leases

    async def get_dhcp_leases(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_dhcp_leases_sync)

    def get_firewall_filters_sync(self) -> List[Dict[str, Any]]:
        """Fetch firewall filter rules."""
        with self.client:
            path = self.client.api.path("ip", "firewall", "filter")
            records = list(path())
            rules = []
            for item in records:
                rules.append({
                    "id": item.get(".id"),
                    "chain": item.get("chain"),
                    "action": item.get("action"),
                    "protocol": item.get("protocol", "all"),
                    "src_address": item.get("src-address", "any"),
                    "dst_address": item.get("dst-address", "any"),
                    "comment": item.get("comment", ""),
                    "disabled": item.get("disabled", False),
                })
            return rules

    async def get_firewall_filters(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_firewall_filters_sync)

    def get_system_logs_sync(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent system logs."""
        with self.client:
            path = self.client.api.path("log")
            records = list(path())
            # Get last records
            records = records[-limit:] if len(records) > limit else records
            results = []
            for item in records:
                results.append({
                    "time": item.get("time"),
                    "topics": item.get("topics"),
                    "message": item.get("message"),
                })
            return results

    async def get_system_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_system_logs_sync, limit)

    def execute_raw_command_sync(self, path_parts: List[str], command_type: str, **kwargs) -> Any:
        """
        Execute configuration change on RouterOS after approval.
        Example:
          path_parts: ['ip', 'firewall', 'filter']
          command_type: 'add'
          kwargs: {'chain': 'forward', 'src_address': '192.168.1.50', 'action': 'drop'}
        """
        with self.client:
            path = self.client.api.path(*path_parts)
            cmd = getattr(path, command_type, None)
            if cmd is None:
                raise ValueError(f"Perintah '{command_type}' tidak dikenali pada path '{'/'.join(path_parts)}'")
            result = cmd(**kwargs)
            return result

    async def execute_raw_command(self, path_parts: List[str], command_type: str, **kwargs) -> Any:
        return await asyncio.to_thread(self.execute_raw_command_sync, path_parts, command_type, **kwargs)

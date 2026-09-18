from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.database import crud
from app.mikrotik.manager import router_manager

router = APIRouter(prefix="/routers/{router_id}/monitoring", tags=["Monitoring"])


async def _get_service_or_404(router_id: int, db: AsyncSession):
    item = await crud.get_router_by_id(db, router_id)
    if not item:
        raise HTTPException(status_code=404, detail="Router not found.")
    service = router_manager.get_service_for_router(item)
    return item, service


@router.get("/resource")
async def get_system_resource(
    router_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch CPU load, RAM usage, uptime, and system info."""
    item, service = await _get_service_or_404(router_id, db)
    try:
        data = await service.get_system_resource()
        return {"router_name": item.name, "resource": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Router connection error: {str(exc)}")


@router.get("/traffic")
async def get_interface_traffic(
    router_id: int,
    interface: str = Query("ether1", description="Interface name (e.g. ether1, wlan1)"),
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch real-time traffic bandwidth (rx/tx bps and packets/sec)."""
    item, service = await _get_service_or_404(router_id, db)
    try:
        data = await service.get_interface_traffic(interface)
        return {"router_name": item.name, "traffic": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch traffic: {str(exc)}")


@router.get("/interfaces")
async def get_interfaces(
    router_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch all network interfaces and their running/disabled status."""
    item, service = await _get_service_or_404(router_id, db)
    try:
        data = await service.get_interfaces()
        return {"router_name": item.name, "interfaces": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch interfaces: {str(exc)}")


@router.get("/dhcp-leases")
async def get_dhcp_leases(
    router_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch connected devices from DHCP server."""
    item, service = await _get_service_or_404(router_id, db)
    try:
        data = await service.get_dhcp_leases()
        return {"router_name": item.name, "dhcp_leases": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch DHCP leases: {str(exc)}")


@router.get("/firewall-filters")
async def get_firewall_filters(
    router_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch active firewall filter rules."""
    item, service = await _get_service_or_404(router_id, db)
    try:
        data = await service.get_firewall_filters()
        return {"router_name": item.name, "firewall_filters": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch firewall rules: {str(exc)}")


@router.get("/logs")
async def get_system_logs(
    router_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """Fetch recent system logs."""
    item, service = await _get_service_or_404(router_id, db)
    try:
        data = await service.get_system_logs(limit=limit)
        return {"router_name": item.name, "logs": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch logs: {str(exc)}")

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.database import crud
from app.schemas.api_schemas import RouterCreateSchema, RouterOutSchema

router = APIRouter(prefix="/routers", tags=["Routers"])


@router.get("", response_model=List[RouterOutSchema])
async def list_routers(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db_session),
):
    """List all registered MikroTik routers."""
    return await crud.get_all_routers(db, active_only=active_only)


@router.post("", response_model=RouterOutSchema, status_code=status.HTTP_201_CREATED)
async def create_router(
    payload: RouterCreateSchema,
    db: AsyncSession = Depends(get_db_session),
):
    """Register a new MikroTik router."""
    existing = await crud.get_router_by_name(db, payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Router with name '{payload.name}' already exists.",
        )

    new_router = await crud.create_router(
        db=db,
        name=payload.name,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        password=payload.password,
        use_ssl=payload.use_ssl,
        description=payload.description,
    )
    return new_router


@router.get("/{router_id}", response_model=RouterOutSchema)
async def get_router_detail(
    router_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Get detail of a specific router."""
    item = await crud.get_router_by_id(db, router_id)
    if not item:
        raise HTTPException(status_code=404, detail="Router not found.")
    return item


@router.delete("/{router_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_router(
    router_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a router from the registry."""
    success = await crud.delete_router(db, router_id)
    if not success:
        raise HTTPException(status_code=404, detail="Router not found.")
    return None

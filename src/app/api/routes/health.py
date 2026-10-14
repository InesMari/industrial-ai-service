from fastapi import APIRouter, Depends
from typing import Annotated
from app.api import router
from app.dependencies.providers import get_modbus_service
from app.services.modbus_service import ModbusService

router = APIRouter(tags=["health"])

@router.get("/health")
async def healh(modbus: Annotated[ModbusService, Depends(get_modbus_service)],):
    return {
        "status": "ok",
        "modbus_connected": modbus._connected,
    }
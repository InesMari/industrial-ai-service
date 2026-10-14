from fastapi import APIRouter, Depends, Query
from typing import Annotated
from app.dependencies.providers import get_modbus_service
from app.services.modbus_service import ModbusService
from app.schemas.common import APIResponse

router = APIRouter(prefix="/sensor", tags=["传感器"])

@router.get("/temperature", response_model=APIResponse)
async def  read_temperature(
    line_id: Annotated[str,Query(pattern=r"^line[1-9]$")],
    modbus: Annotated[ModbusService, Depends(get_modbus_service)],
):
    reading = await modbus.read_temperature(line_id)
    return APIResponse(data = reading)

    
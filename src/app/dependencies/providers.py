from functools import lru_cache
from app.core.config import get_settings, setting
from app.services.modbus_service import ModbusService

@lru_cache
def get_modbus_service() -> ModbusService :
    settings = get_settings()
    return ModbusService(
        host=settings.MODBUS_HOST,
        port=settings.MODBUS_PORT,
        slave_id=settings.MODBUS_SLAVE_ID,
        timeout=settings.MODBUS_TIMEOUT,
    )
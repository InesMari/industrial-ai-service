from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class LoopResult(BaseModel):
    timestamp: datetime
    temperature: float
    pressure: float
    vibration: float
    severity: Literal["normal", "warning", "alarm"]
    trend: Literal["stable", "rising", "falling"]
    message: str
    action_taken: str
    modbus_coils: dict = {}
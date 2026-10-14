from pydantic import BaseModel, Field
from typing import Annotated
from datetime import datetime  

class SensorReading(BaseModel):
    line_id: Annotated[str, Field(pattern=r"^line[1-9]$")]
    temperature: float = Field(ge=-50, le=200, description="温度，单位°C")
    pressure: float = Field(ge=0, le=2000, description="压力，单位kPa")
    timestamp: datetime = Field(default_factory=datetime.now)

class DeviceCommand(BaseModel):
    device_id: Annotated[str, Field(min_length=1, max_length=50)]
    action: Annotated[str, Field(pattern=r"^(start|stop|reset)$")]
    command_id: str = Field(description="幂等ID")
import pytest
from app.services.collector import ClosedLoopCollector


class FakeModbus:
    _connected = True

    def __init__(self):
        self.temperature = 25.0
        self.vibration = 1.5
        self.pressure = 101.3
        self.coils = {0: False, 1: False}

    async def read_sensor_data(self):
        return {
            "temperature": self.temperature,
            "pressure": self.pressure,
            "vibration": self.vibration,
        }

    async def write_coil(self, address, value):
        self.coils[address] = value

    async def read_coils(self):
        return {
            "alarm_light": self.coils[0],
            "cooling_valve": self.coils[1],
        }


class FakeOpcUa:
    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def subscribe(self, paths, on_change=None):
        pass


@pytest.mark.asyncio
async def test_judge_normal():
    modbus = FakeModbus()
    collector = ClosedLoopCollector(modbus, FakeOpcUa())
    severity, trend, msg = collector._judge(25.0, 1.5)
    assert severity == "normal"


@pytest.mark.asyncio
async def test_judge_alarm_temperature():
    modbus = FakeModbus()
    collector = ClosedLoopCollector(modbus, FakeOpcUa())
    severity, _, _ = collector._judge(36.0, 1.5)
    assert severity == "alarm"


@pytest.mark.asyncio
async def test_run_once_writes_coil_on_alarm():
    modbus = FakeModbus()
    modbus.temperature = 36.0
    collector = ClosedLoopCollector(modbus, FakeOpcUa())
    result = await collector._run_once()
    assert result.severity == "alarm"
    assert modbus.coils[0] is True   # 报警灯
    assert modbus.coils[1] is True   # 冷却阀
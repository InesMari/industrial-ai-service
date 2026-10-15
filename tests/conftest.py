import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.dependencies.providers import get_modbus_service
from app.core.exceptions import DeviceOfflineError


class FakeModbusService:
    def __init__(self):
        self._connected = True
        self._temperature = 25.0
        self._should_fail = False

    async def connect(self):
        self._connected = True

    async def disconnect(self):
        self._connected = False

    async def read_temperature(self, line_id: str) -> dict:
        if self._should_fail:
            raise DeviceOfflineError(f"modbus@{line_id}")
        if not self._connected:
            raise DeviceOfflineError("modbus")
        return {
            "line_id": line_id,
            "temperature": self._temperature,
            "pressure": 1013.0,
            "unit": "celsius",
        }

    def set_temperature(self, value: float):
        self._temperature = value

    def set_fail(self, fail: bool):
        self._should_fail = fail


@pytest.fixture
def fake_modbus():                    # ← 独立 fixture
    return FakeModbusService()


@pytest.fixture
def app(fake_modbus):                 # ← app 依赖 fake_modbus
    app = create_app()
    app.dependency_overrides[get_modbus_service] = lambda: fake_modbus
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
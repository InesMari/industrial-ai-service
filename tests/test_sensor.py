import pytest


@pytest.mark.asyncio
async def test_read_temperature_success(client, fake_modbus):
    """正常读取温度"""
    fake_modbus.set_temperature(28.5)

    resp = await client.get("/api/v1/sensor/temperature?line_id=line1")

    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["line_id"] == "line1"
    assert data["data"]["temperature"] == 28.5
    assert data["data"]["unit"] == "celsius"


@pytest.mark.asyncio
async def test_read_temperature_invalid_line_id(client):
    """产线编号不合法，返回 422"""
    resp = await client.get("/api/v1/sensor/temperature?line_id=line99")

    assert resp.status_code == 422
    data = resp.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "请求参数不合法"


@pytest.mark.asyncio
async def test_read_temperature_missing_param(client):
    """缺少必填参数，返回 422"""
    resp = await client.get("/api/v1/sensor/temperature")

    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_read_temperature_device_offline(client, fake_modbus):
    """设备离线，返回 503"""
    fake_modbus.set_fail(True)

    resp = await client.get("/api/v1/sensor/temperature?line_id=line1")

    assert resp.status_code == 503
    data = resp.json()
    assert data["code"] == "DEVICE_OFFLINE"
    assert "离线" in data["message"]
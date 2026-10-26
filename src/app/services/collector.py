"""
闭环采集器：触发 → 采集 → 判定 → 输出。
作为后台异步任务运行，挂到 FastAPI lifespan 上。
"""
import asyncio
import logging
import json
from collections import deque
from datetime import datetime

import paho.mqtt.client as mqtt

from app.services.modbus_service import ModbusService, ALARM_COIL, COOLING_COIL
from app.services.opcua_service import OpcUaService
from app.schemas.closed_loop import LoopResult

logger = logging.getLogger(__name__)

# 判定阈值
TEMP_WARNING = 30.0
TEMP_ALARM = 35.0
VIB_WARNING = 2.5
VIB_ALARM = 3.5


class ClosedLoopCollector:
    def __init__(
        self,
        modbus: ModbusService,
        opcua: OpcUaService,
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        mqtt_prefix: str = "factory",
        interval: float = 2.0,
    ):
        self.modbus = modbus
        self.opcua = opcua
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_prefix = mqtt_prefix
        self.interval = interval

        self._running = False
        self._task = None
        self._mqtt = mqtt.Client()
        self._mqtt_connected = False

        self.history: deque[LoopResult] = deque(maxlen=100)
        self.latest: LoopResult | None = None

        # OPC UA 订阅的最新值
        self._opcua_latest: dict = {}

    def _on_opcua_change(self, name: str, val):
        self._opcua_latest[name] = val

    async def start(self):
        """启动采集器：连接 OPC UA 并订阅，启动后台循环。"""
        self._running = True

        # 连接 OPC UA 并订阅（带重试，等待 opcua-sim 就绪）
        last_error = None
        for attempt in range(10):
            try:
                await self.opcua.connect()
                break
            except Exception as e:
                last_error = e
                logger.warning(f"OPC UA 连接失败，第 {attempt + 1} 次重试: {e}")
                await asyncio.sleep(2)
        else:
            raise RuntimeError(f"OPC UA 连接失败，已重试 10 次: {last_error}")

        await self.opcua.subscribe(
            ["ProductionLine/Temperature", "ProductionLine/Vibration"],
            on_change=self._on_opcua_change,
        )

        # 连接 MQTT（失败不影响闭环）
        try:
            self._mqtt.connect(self.mqtt_broker, self.mqtt_port, 60)
            self._mqtt.loop_start()
            self._mqtt_connected = True
            logger.info(f"MQTT 已连接 {self.mqtt_broker}:{self.mqtt_port}")
        except Exception as e:
            logger.warning(f"MQTT 连接失败（闭环继续运行）: {e}")
            self._mqtt_connected = False

        self._task = asyncio.create_task(self._loop())
        logger.info("闭环采集器已启动")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.opcua.disconnect()
        if self._mqtt_connected:
            self._mqtt.loop_stop()
            self._mqtt.disconnect()
        logger.info("闭环采集器已停止")

    async def _loop(self):
        """主循环：每 interval 秒执行一次完整闭环。"""
        while self._running:
            try:
                result = await self._run_once()
                self.latest = result
                self.history.append(result)
            except Exception as e:
                logger.exception(f"闭环执行异常: {e}")
            await asyncio.sleep(self.interval)

    async def _run_once(self) -> LoopResult:
        """一次完整闭环：触发 → 采集 → 判定 → 输出。"""

        # ===== 1. 触发 =====
        logger.debug("闭环触发")

        # ===== 2. 采集 =====
        # Modbus 读温度、压力、振动
        modbus_data = await self.modbus.read_sensor_data()
        temperature = modbus_data["temperature"]
        pressure = modbus_data["pressure"]
        vibration = modbus_data["vibration"]

        # OPC UA 订阅值优先（如果收到了）
        opcua_vib = self._opcua_latest.get("ProductionLine/Vibration")
        if opcua_vib is not None:
            vibration = opcua_vib

        # ===== 3. 判定 =====
        severity, trend, message = self._judge(temperature, vibration)

        # ===== 4. 输出 =====
        action_taken = ""
        if severity == "alarm":
            await self.modbus.write_coil(ALARM_COIL, True)
            await self.modbus.write_coil(COOLING_COIL, True)
            action_taken = "报警灯亮 + 冷却阀开"
            logger.warning(f"报警: {message} | 动作: {action_taken}")
            self._publish_mqtt("alarm", {
                "temperature": temperature,
                "vibration": vibration,
                "message": message,
            })
        elif severity == "warning":
            await self.modbus.write_coil(ALARM_COIL, False)
            await self.modbus.write_coil(COOLING_COIL, True)
            action_taken = "冷却阀开"
            logger.info(f"预警: {message} | 动作: {action_taken}")
            self._publish_mqtt("warning", {
                "temperature": temperature,
                "vibration": vibration,
                "message": message,
            })
        else:
            await self.modbus.write_coil(ALARM_COIL, False)
            await self.modbus.write_coil(COOLING_COIL, False)
            action_taken = "无"

        # 发布遥测
        self._publish_mqtt("telemetry", {
            "temperature": temperature,
            "pressure": pressure,
            "vibration": vibration,
            "severity": severity,
            "trend": trend,
        })

        coils = await self.modbus.read_coils()

        return LoopResult(
            timestamp=datetime.now(),
            temperature=temperature,
            pressure=pressure,
            vibration=vibration,
            severity=severity,
            trend=trend,
            message=message,
            action_taken=action_taken,
            modbus_coils=coils,
        )

    def _judge(self, temperature: float, vibration: float) -> tuple:
        """判定逻辑：阈值 + 趋势。"""
        trend = "stable"
        if len(self.history) >= 5:
            recent = [r.temperature for r in list(self.history)[-5:]]
            if recent[-1] - recent[0] > 1.0:
                trend = "rising"
            elif recent[0] - recent[-1] > 1.0:
                trend = "falling"

        if temperature >= TEMP_ALARM or vibration >= VIB_ALARM:
            return "alarm", trend, (
                f"温度 {temperature:.1f}°C / 振动 {vibration:.2f}mm/s 超报警阈值"
            )
        elif temperature >= TEMP_WARNING or vibration >= VIB_WARNING:
            return "warning", trend, (
                f"温度 {temperature:.1f}°C / 振动 {vibration:.2f}mm/s 超预警阈值"
            )
        else:
            return "normal", trend, "参数正常"

    def _publish_mqtt(self, channel: str, payload: dict):
        if not self._mqtt_connected:
            return
        topic = f"{self.mqtt_prefix}/line1/{channel}"
        try:
            self._mqtt.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1)
        except Exception as e:
            logger.warning(f"MQTT 发布失败: {e}")
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class LoopResult(BaseModel):
    timestamp: datetime     # 闭环判定的时间戳，精确到秒或毫秒
    temperature: float      # 当前温度，单位 °C，保留 1 位小数
    pressure: float         # 当前压力，单位 kPa，保留 1 位小数
    vibration: float        # 当前振动速度，单位 mm/s，保留 2 位小数
    severity: Literal["normal", "warning", "alarm"]     # 判定等级，三档：正常 / 预警 / 报警
    trend: Literal["stable", "rising", "falling"]       # 温度趋势，三档：平稳 / 上升 / 下降
    message: str            # 判定说明，比如"温度 32.5°C 超预警阈值"
    action_taken: str       # 本次闭环实际执行了什么动作，比如"报警灯亮 + 冷却阀开"
    modbus_coils: dict = {} # 本次写回的线圈状态快照，比如 {0: True, 1: True}，键是线圈地址，值是布尔
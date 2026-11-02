import logging
from langchain.tools import tool
from app.dependencies.providers import get_modbus_service

logger = logging.getLogger(__name__)

@tool
async def read_sensor_data(line_id: str):
    """读取指定产线的实时传感器数据（温度、压力、振动）。    
    Args:
        line_id: 产线编号，格式为 line1 到 line9，例如 "line1"    
    Returns:
        包含 temperature、pressure、vibration 的字典
    """
    logger.info(f"[Tool] read_sensor_data(line_id={line_id})")
    modbus = get_modbus_service()
    data = await modbus.read_sensor_data()
    return {
        "line_id": line_id,
        "temperature": data["temperature"],
        "pressure": data["pressure"],
        "vibration": data["vibration"],
    }

@tool
async def query_equipment_manual(query: str):
    """检索设备手册、工艺规范、质检标准等工业知识。    
    Args:
        query: 自然语言查询，例如 "焊接气孔允许范围"    
    Returns:
        检索到的知识片段
    """
    logger.info(f"[Tool] query_equipment_manual(query={query})")
    # 真实场景：接入你的RAG检索服务
    # chunks = await rag_service.retrieve(query)
    # return "\n".join([c["content"] for c in chunks])
    return f"根据《焊接工艺规范》第3.2条，关于'{query}'的规定是：允许范围为..."

@tool
async def trigger_alarm(line_id: str, reason: str):
    """触发产线报警（高危操作，会写PLC线圈并发送MQTT告警）。    
    Args:
        line_id: 产线编号
        reason: 报警原因    
    Returns:
        操作结果
    """
    logger.info(f"[Tool] trigger_alarm(line_id={line_id}, reason={reason})")
    modbus = get_modbus_service()
    await modbus.write_coil(0, True)   # 报警灯
    await modbus.write_coil(1, True)   # 冷却阀
    return f"已触发 {line_id} 报警：{reason}"

# 导出工具列表，方便后续绑定
INDUSTRIAL_TOOLS = [read_sensor_data, query_equipment_manual, trigger_alarm]
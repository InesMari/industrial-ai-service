from fastapi import APIRouter, Request
from app.schemas.common import APIResponse

router = APIRouter(prefix="/closed-loop", tags=["闭环"])

@router.get("/status", response_model=APIResponse)
async def get_status(request: Request):
    """获取闭环最新状态。"""
    collector = request.app.state.collector
    latest = collector.latest
    if latest is None:
        return APIResponse(data={"message": "采集器尚未产出结果"})
    return APIResponse(data=latest.model_dump(mode="json"))

@router.get("/history", response_model=APIResponse)
async def get_history(request: Request, limit: int = 20):
    """获取最近 N 条判定记录。"""
    collector = request.app.state.collector
    records = list(collector.history)[-limit:]
    return APIResponse(data=[r.model_dump(mode="json") for r in records])



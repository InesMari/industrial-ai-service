from fastapi import APIRouter, UploadFile, Request
from app.schemas.common import APIResponse

router = APIRouter(prefix="/vision", tags=["视觉"])

@router.post("/neu-det/detect", response_model=APIResponse)
async def detect_neu(request: Request, file: UploadFile):
    service = request.app.state.vision
    detections = service.detect(await file.read())
    return APIResponse(data={"defect_count": len(detections), "detections": detections})
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.core.exceptions import AppException
from app.api.router import api_router
from app.dependencies.providers import get_modbus_service

settings = get_settings()
setup_logging(settings.APP_LOG_LEVEL)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("服务器启动中......")
    modbus = get_modbus_service()
    await modbus.connect()
    logger.info("服务器启动完成")
    yield
    logger.info("服务器正在关闭......")
    await modbus.disconnect()
    logger.info("服务器已关闭")

def create_app() -> FastAPI:
    app = FastAPI(
        title = "工业AI数据服务", 
        version = "0.0.1",
        lifespan = lifespan,
    )
    
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(AppException)
    async def exception_handler(request:Request, exc: AppException):
        rid = getattr(request.state, "request_id", None)
        logger.error(f"业务异常: {exc.code} - {exc.message}", extra={"request_id": rid})
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        rid = getattr(request.state, "request_id", None)
        logger.warning(f"参数校验失败: {exc.errors()}", extra={"request_id": rid})
        return JSONResponse(
            status_code=422,
            content={"code": "VALIDATION_ERROR", "message": "请求参数不合法", "data": None},
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        rid = getattr(request.state, "request_id", None)
        logger.exception("未预期异常", extra={"request_id": rid})
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_ERROR", "message": "服务内部错误", "data": None},
        )
    @app.get("/health")
    def root():
        return {"message": "Hello World"}

    @app.get("/test/business-error")
    async def test_business_error():
        from app.core.exceptions import DeviceOfflineError
        raise DeviceOfflineError("modbus@192.168.1.10")

    @app.get("/test/unknown-error")
    async def test_unknown_error():
        raise RuntimeError("这是一个未预期的异常")

    app.include_router(api_router, prefix="/api/v1")
    return app

app = create_app()

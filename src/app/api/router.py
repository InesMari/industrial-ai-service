from fastapi import APIRouter
from app.api.routes import sensor, health, closed_loop

api_router = APIRouter()
api_router.include_router(sensor.router)
api_router.include_router(health.router)
api_router.include_router(closed_loop.router)
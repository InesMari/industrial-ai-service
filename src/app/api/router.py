from fastapi import APIRouter
from app.api.routes import sensor, health

api_router = APIRouter()
api_router.include_router(sensor.router)
api_router.include_router(health.router)
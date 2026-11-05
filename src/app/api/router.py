from fastapi import APIRouter
from app.api.routes import sensor, health, closed_loop, agent, vision

api_router = APIRouter()
api_router.include_router(sensor.router)
api_router.include_router(health.router)
api_router.include_router(closed_loop.router)
api_router.include_router(agent.router)
api_router.include_router(vision.router)
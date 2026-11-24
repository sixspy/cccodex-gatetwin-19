from fastapi import APIRouter
from app.routers import 核心

api = APIRouter()
api.include_router(核心.路由)

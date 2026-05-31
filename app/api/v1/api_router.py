"""
Master router for API v1.0.0
Includes all sub-routers for different resource types (e.g. staff, patients, appointments)
"""

from fastapi import APIRouter

from app.api.v1.routers import users_router

api_router = APIRouter()

api_router.include_router(users_router.router)

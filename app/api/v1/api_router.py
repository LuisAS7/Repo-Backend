"""
Master router for API v1.0.0
Includes all sub-routers for different resource types (e.g. staff, patients, appointments)
"""

from fastapi import APIRouter

from app.api.v1.routers import appointments_router, patients_router, users_router, catalogs_router, triage_router

api_router = APIRouter()

api_router.include_router(users_router.router)
api_router.include_router(patients_router.router)
api_router.include_router(catalogs_router.router)
api_router.include_router(appointments_router.router)
api_router.include_router(triage_router.router)

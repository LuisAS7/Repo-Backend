"""
Master router for API v1.0.0
Includes all sub-routers for different resource types (e.g. staff, patients, appointments)
"""

from fastapi import APIRouter

from app.api.v1.routers.appointments_router import router as appointments_router
from app.api.v1.routers.auth_router import router as auth_router
from app.api.v1.routers.catalogs_router import router as catalogs_router
from app.api.v1.routers.patients_router import router as patients_router
from app.api.v1.routers.triage_router import router as triage_router
from app.api.v1.routers.users_router import router as users_router

api_router = APIRouter()

# ── Public routes (no authentication required) ───────────────────────────────
api_router.include_router(auth_router)

# ── Protected routes ─────────────────────────────────────────────────────────
api_router.include_router(users_router)
api_router.include_router(patients_router)
api_router.include_router(appointments_router)
api_router.include_router(catalogs_router)
api_router.include_router(triage_router)

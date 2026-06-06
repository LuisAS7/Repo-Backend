"""
Central API router that aggregates all sub-routers.

Protected routers should be included with:

    from app.api.deps import get_current_user

    api_router.include_router(
        patients_router,
        prefix="/patients",
        tags=["Patients"],
        dependencies=[Depends(get_current_user)],
    )

This ensures every endpoint in the router requires a valid JWT token
without having to repeat the dependency in each individual route handler.
"""

from fastapi import APIRouter

from app.api.v1.routers.auth_router import router as auth_router

api_router = APIRouter()

# ── Public routes (no authentication required) ───────────────────────────────
api_router.include_router(auth_router)

# ── Protected routes ─────────────────────────────────────────────────────────
# Uncomment each block below as the corresponding router is implemented.
#
# from app.api.patients_router import router as patients_router
# api_router.include_router(
#     patients_router,
#     prefix="/patients",
#     tags=["Patients"],
#     dependencies=[Depends(get_current_user)],
# )
#
# from app.api.appointments_router import router as appointments_router
# api_router.include_router(
#     appointments_router,
#     prefix="/appointments",
#     tags=["Appointments"],
#     dependencies=[Depends(get_current_user)],
# )
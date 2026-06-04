"""
Global exception handlers
Maps internal business logic exceptions to standardized HTTP responses
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    BaseBusinessException,
    ConflictError,
    NotFoundError,
    ValidationError,
)

# Set up a logger for this module
logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Registers all custom exception handlers to the FastAPI app instance"""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        logger.info(f"Not Found: {exc.message} - Path: {request.url.path}")
        return JSONResponse(status_code=404, content={"error": "Not Found", "message": exc.message})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        logger.warning(f"Conflict: {exc.message} - Path: {request.url.path}")
        return JSONResponse(status_code=409, content={"error": "Conflict", "message": exc.message})

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        logger.warning(f"Validation Error: {exc.message} - Path: {request.url.path}")
        return JSONResponse(status_code=422, content={"error": "Unprocessable Entity", "message": exc.message})

    @app.exception_handler(AuthenticationError)
    async def authentication_handler(request: Request, exc: AuthenticationError):
        logger.warning(f"Authentication Failed: {exc.message} - Path: {request.url.path}")
        return JSONResponse(status_code=401, content={"error": "Unauthorized", "message": exc.message})

    # Fallback handler for any other business exceptions not explicitly handled above
    @app.exception_handler(BaseBusinessException)
    async def generic_business_handler(request: Request, exc: BaseBusinessException):
        logger.error(f"Generic Business Error: {exc.message} - Path: {request.url.path}")
        return JSONResponse(status_code=400, content={"error": "Bad Request", "message": exc.message})

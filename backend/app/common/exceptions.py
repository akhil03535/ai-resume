"""
Structured, user-safe exceptions.

Every raised error here maps to a clean JSON response and a specific HTTP
status. Internal details (stack traces, DB errors, AI provider payloads)
are logged server-side but never leaked to the client (see spec #31/#36).
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("resumeai")


class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(self, message: str, code: str | None = None, status_code: int | None = None):
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class FileProcessingError(AppError):
    status_code = 422
    code = "file_processing_error"


class AIProviderError(AppError):
    status_code = 502
    code = "ai_provider_error"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Something went wrong. Please try again."}},
        )

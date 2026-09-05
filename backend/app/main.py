import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.common.exceptions import register_exception_handlers

# Import every model module so SQLAlchemy's mapper registry is fully
# populated before any relationship is resolved (important for Alembic
# autogenerate and for cross-module relationship() string references).
from app.users import models as _users_models  # noqa: F401
from app.profiles import models as _profiles_models  # noqa: F401
from app.skills import models as _skills_models  # noqa: F401
from app.jobs import models as _jobs_models  # noqa: F401
from app.resumes import models as _resumes_models  # noqa: F401
from app.analysis import models as _analysis_models  # noqa: F401

from app.auth.router import router as auth_router
from app.profiles.router import router as profiles_router
from app.resumes.router import router as resumes_router
from app.jobs.router import router as jobs_router
from app.skills.router import router as skills_router
from app.analysis.router import router as analysis_router
from app.generator.router import router as generator_router
from app.dashboard.router import router as dashboard_router

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)

app = FastAPI(title=settings.APP_NAME, debug=False)
# `debug` is deliberately hardcoded to False here, independent of
# settings.DEBUG - Starlette's debug mode renders raw tracebacks (full
# internal file paths, SQLAlchemy/library internals, doc links) directly
# into the HTTP response body, which can bypass the custom exception
# handlers registered below. That must never reach a client under any
# circumstances (spec: "Frontend should never receive raw Traceback").
# settings.DEBUG still controls logging verbosity and other genuinely safe
# dev conveniences - see core/config.py.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(skills_router)
app.include_router(analysis_router)
app.include_router(generator_router)
app.include_router(dashboard_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

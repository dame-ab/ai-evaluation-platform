from fastapi import APIRouter

from app.api.routes import (
    analytics,
    evaluations,
    login,
    private,
    projects,
    rubrics,
    tasks,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(projects.router)
api_router.include_router(rubrics.router)
api_router.include_router(tasks.router)
api_router.include_router(evaluations.router)
api_router.include_router(analytics.router)


if settings.FASTAPI_ENV == "development":
    api_router.include_router(private.router)

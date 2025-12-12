from fastapi import APIRouter
from app.api.v1 import auth, jobs, documents, interviews, matcher

# Main API router
api_router = APIRouter()

# Include all module routers
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(documents.router)
api_router.include_router(interviews.router)
api_router.include_router(matcher.router)

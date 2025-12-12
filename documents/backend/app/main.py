from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base
from sqlalchemy import text

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI-powered HR & Talent Management Platform for DHL Hackathon",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configure CORS - MUST be added before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:6173",
        "http://127.0.0.1:6173",
        "http://localhost:6174",
        "http://127.0.0.1:6174",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


@app.on_event("startup")
async def on_startup():
    """Ensure all tables exist at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight migration: add missing columns if schema changed
        # Ensure generated_documents.email_hash exists
        try:
            result = await conn.execute(text("PRAGMA table_info('generated_documents')"))
            cols = [row[1] for row in result.fetchall()]
            if 'email_hash' not in cols:
                await conn.execute(text("ALTER TABLE generated_documents ADD COLUMN email_hash VARCHAR"))
        except Exception as e:
            # Log and continue; do not block startup
            print(f"Schema check/migration skipped due to error: {type(e).__name__}: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Talent Connect API",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production"
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

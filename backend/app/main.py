"""SENTINEL FastAPI Application Entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import (
    telemetry_router,
    incidents_router,
    health_router,
    demo_router,
    projects_router,
    radar_router,
    validation_router,
)

app = FastAPI(
    title=settings.app_name,
    description="AI-powered developer intelligence platform for project ingestion, incident correlation, root-cause ranking, and telemetry ingestion.",
    version="1.0.0",
)

# CORS middleware for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(telemetry_router, prefix=settings.api_prefix)
app.include_router(incidents_router, prefix=settings.api_prefix)
app.include_router(demo_router, prefix=settings.api_prefix)
app.include_router(projects_router, prefix=settings.api_prefix)
app.include_router(radar_router, prefix=settings.api_prefix)
app.include_router(validation_router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {
        "platform": settings.app_name,
        "docs_url": "/docs",
        "api_prefix": settings.api_prefix,
        "status": "operational",
    }

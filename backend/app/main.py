from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings, validate_production_configuration
from .routes import (
    telemetry_router,
    incidents_router,
    health_router,
    demo_router,
    projects_router,
    radar_router,
    validation_router,
    rag_router,
)
from .services.rag import initialize_knowledge_base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup validation, indexing, and graceful shutdown."""
    try:
        validate_production_configuration()
    except Exception as e:
        print(f"Warning: Production configuration validation error: {e}")
    try:
        initialize_knowledge_base()
    except Exception as e:
        print(f"Warning: Failed to auto-index knowledge base on startup: {e}")
    yield

app = FastAPI(
    title=settings.app_name,
    description="AI-powered developer intelligence platform for project ingestion, incident correlation, root-cause ranking, and telemetry ingestion.",
    version="1.0.0",
    lifespan=lifespan,
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.environment.lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Secure CORS middleware: never allow credentials if origin is wildcard
has_wildcard = "*" in settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=not has_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global unhandled exception handler: sanitize error details in production
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if not settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred.",
                "status": 500,
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "status": 500,
        },
    )

# Include API routers under /api
app.include_router(health_router, prefix=settings.api_prefix)
# Also register health router at root for direct /health access
app.include_router(health_router)
app.include_router(telemetry_router, prefix=settings.api_prefix)
app.include_router(incidents_router, prefix=settings.api_prefix)
app.include_router(demo_router, prefix=settings.api_prefix)
app.include_router(projects_router, prefix=settings.api_prefix)
app.include_router(radar_router, prefix=settings.api_prefix)
app.include_router(validation_router, prefix=settings.api_prefix)
app.include_router(rag_router, prefix=settings.api_prefix)


@app.get("/")
@app.get("/api")
@app.get("/api/")
@app.get("/api/index.py")
@app.get("/api/index")
async def root():
    return {
        "platform": settings.app_name,
        "docs_url": "/docs",
        "api_prefix": settings.api_prefix,
        "status": "operational",
    }

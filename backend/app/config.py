"""Configuration settings for SENTINEL Backend."""
import os
import tempfile
from typing import List, Optional
from pydantic import BaseModel

def _get_blob_token() -> Optional[str]:
    candidates = [
        "BLOB_READ_WRITE_TOKEN",
        "SENTINEL_PROJECT_UPLOADS_READ_WRITE_TOKEN",
        "SENTINEL_PROJECT_UPLOADS_BLOB_READ_WRITE_TOKEN",
    ]
    for key in candidates:
        val = os.getenv(key)
        if val and val.strip():
            return val.strip().strip('"').strip("'")
    for key, val in os.environ.items():
        if key.endswith("_READ_WRITE_TOKEN") and val and val.strip():
            return val.strip().strip('"').strip("'")
    return None

def _get_cors_origins() -> List[str]:
    raw = os.getenv("SENTINEL_CORS_ORIGINS")
    default_dev_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    production_origins = ["https://sentinel-7f6f.vercel.app"]
    if raw:
        origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
        if "https://sentinel-7f6f.vercel.app" not in origins:
            origins.append("https://sentinel-7f6f.vercel.app")
        # Preserve local development origins if not running in production
        if os.getenv("SENTINEL_ENV", "development").lower() != "production":
            for d in default_dev_origins:
                if d not in origins:
                    origins.append(d)
        return origins
    return default_dev_origins + production_origins

def _get_default_data_dir() -> str:
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return os.path.join(tempfile.gettempdir(), "sentinel_data")
    return os.path.join(os.getcwd(), "data")

def _get_default_projects_dir() -> str:
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return os.path.join(tempfile.gettempdir(), "sentinel_projects")
    return os.path.join(os.getcwd(), "data", "projects")

class Settings(BaseModel):
    app_name: str = "SENTINEL — Developer Intelligence Platform"
    api_prefix: str = "/api"
    environment: str = os.getenv("SENTINEL_ENV", "development")
    debug: bool = os.getenv("SENTINEL_DEBUG", "true").lower() in ("true", "1")
    cors_origins: List[str] = _get_cors_origins()

    # Authentication & Multi-Tenant Isolation
    auth_enabled: bool = os.getenv("SENTINEL_AUTH_ENABLED", "false").lower() in ("true", "1")
    secret_key: str = os.getenv("SENTINEL_SECRET_KEY", "sentinel-insecure-default-signing-key-change-in-prod")
    api_key: str = os.getenv("SENTINEL_API_KEY", "demo-sentinel-key-2026")
    admin_api_key: str = os.getenv("SENTINEL_ADMIN_API_KEY", "admin-sentinel-key-2026")

    # Rate Limiting & Networking
    behind_trusted_proxy: bool = os.getenv("BEHIND_TRUSTED_PROXY", "false").lower() in ("true", "1")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    expensive_rate_limit_per_minute: int = int(os.getenv("EXPENSIVE_RATE_LIMIT_PER_MINUTE", "30"))
    max_telemetry_batch_size: int = int(os.getenv("MAX_TELEMETRY_BATCH_SIZE", "1000"))

    # Incident detection thresholds
    error_spike_threshold: int = 3
    correlation_window_seconds: float = 300.0  # 5 minutes
    deduplication_cache_size: int = 10000

    # Project Ingestion & Storage Settings
    data_dir: str = _get_default_data_dir()
    projects_dir: str = _get_default_projects_dir()
    
    # Upload limits
    blob_read_write_token: Optional[str] = _get_blob_token()
    max_upload_size_bytes: int = 50 * 1024 * 1024       # 50 MB
    max_extracted_size_bytes: int = 150 * 1024 * 1024   # 150 MB
    max_archive_entries: int = 5000                     # Max files/dirs in ZIP
    
    # Security exclusions (skipped from extraction & analysis)
    excluded_patterns: List[str] = [
        # Secrets and credentials
        ".env", ".env.*", "*.pem", "*.key", "id_rsa", "id_ed25519", "*.pfx", "*.pkcs12",
        # Dependencies & virtual environments
        "node_modules", ".venv", "venv", "env", "vendor",
        # Version control & cache
        ".git", ".svn", ".hg", "__pycache__", ".pytest_cache", ".cache",
        # Build artifacts
        "dist", "build", "target", "out", "*.pyc", "*.pyo", ".DS_Store"
    ]
    
    # Suspicious binary / executable extensions to reject
    prohibited_extensions: List[str] = [
        ".exe", ".dll", ".so", ".dylib", ".bin", ".com", ".scr"
    ]

settings = Settings()

def validate_production_configuration() -> None:
    """Validate environment settings at startup to prevent running insecure production deployments."""
    if settings.environment.lower() == "production":
        errors = []
        if not settings.auth_enabled:
            errors.append("SENTINEL_AUTH_ENABLED must be 'true' in production.")
        if settings.secret_key == "sentinel-insecure-default-signing-key-change-in-prod":
            errors.append("SENTINEL_SECRET_KEY must be configured with a secure random key in production.")
        if settings.api_key == "demo-sentinel-key-2026":
            errors.append("SENTINEL_API_KEY must be changed from the default demo key in production.")
        if settings.admin_api_key == "admin-sentinel-key-2026":
            errors.append("SENTINEL_ADMIN_API_KEY must be changed from the default admin key in production.")
        if any("localhost" in origin or "127.0.0.1" in origin for origin in settings.cors_origins):
            errors.append("SENTINEL_CORS_ORIGINS must not contain localhost or 127.0.0.1 in production.")
        if "*" in settings.cors_origins:
            errors.append("SENTINEL_CORS_ORIGINS must not contain wildcard '*' in production.")
        if errors:
            raise RuntimeError("Production security validation failed:\n - " + "\n - ".join(errors))

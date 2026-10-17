"""Configuration settings for SENTINEL Backend."""
import os
from typing import List
from pydantic import BaseModel

def _get_cors_origins() -> List[str]:
    raw = os.getenv("SENTINEL_CORS_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

class Settings(BaseModel):
    app_name: str = "SENTINEL — Developer Intelligence Platform"
    api_prefix: str = "/api"
    environment: str = os.getenv("SENTINEL_ENV", "development")
    debug: bool = os.getenv("SENTINEL_DEBUG", "true").lower() in ("true", "1")
    cors_origins: List[str] = _get_cors_origins()

    # Authentication & Multi-Tenant Isolation
    auth_enabled: bool = os.getenv("SENTINEL_AUTH_ENABLED", "false").lower() in ("true", "1")
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
    data_dir: str = os.path.join(os.getcwd(), "data")
    projects_dir: str = os.path.join(os.getcwd(), "data", "projects")
    
    # Upload limits
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


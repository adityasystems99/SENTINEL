"""Configuration settings for SENTINEL Backend."""
import os
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "SENTINEL — Developer Intelligence Platform"
    api_prefix: str = "/api"
    debug: bool = True
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    # Incident detection thresholds
    error_spike_threshold: int = 3
    correlation_window_seconds: float = 300.0  # 5 minutes
    deduplication_cache_size: int = 10000

settings = Settings()

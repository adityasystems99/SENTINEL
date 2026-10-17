"""Configuration settings for SENTINEL Backend."""
import os
from typing import List
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "SENTINEL — Developer Intelligence Platform"
    api_prefix: str = "/api"
    debug: bool = True
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
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

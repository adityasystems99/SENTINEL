import os
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/api
_backend_dir = os.path.dirname(_current_dir)              # backend

# Prioritize backend_dir in sys.path
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
elif sys.path[0] != _backend_dir:
    sys.path.remove(_backend_dir)
    sys.path.insert(0, _backend_dir)

# Only append parent directory if running locally inside Sentinel/backend (never on /var)
if os.path.basename(_backend_dir) == "backend":
    _repo_root = os.path.dirname(_backend_dir)
    if os.path.exists(_repo_root) and _repo_root not in sys.path:
        sys.path.append(_repo_root)

# Resolve module namespace conflict:
if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

if "demo_app" in sys.modules and not hasattr(sys.modules["demo_app"], "__path__"):
    del sys.modules["demo_app"]

try:
    from app.main import app
except Exception:
    try:
        from backend.app.main import app
    except Exception as _startup_err:
        import traceback
        _tb = traceback.format_exc()
        from fastapi import FastAPI
        from fastapi.responses import PlainTextResponse

        app = FastAPI(title="SENTINEL Startup Diagnostics")

        @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        async def _handle_startup_error(full_path: str):
            return PlainTextResponse(f"SENTINEL STARTUP ERROR:\n{_tb}", status_code=500)

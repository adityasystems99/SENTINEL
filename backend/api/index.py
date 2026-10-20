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
# If root app.py was loaded into sys.modules['app'] as a single-file module (lacking __path__),
# evict it so Python resolves the actual backend/app package.
if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

if "demo_app" in sys.modules and not hasattr(sys.modules["demo_app"], "__path__"):
    del sys.modules["demo_app"]

try:
    from app.main import app as _raw_app
except Exception:
    try:
        from backend.app.main import app as _raw_app
    except Exception as _startup_err:
        import traceback
        _tb = traceback.format_exc()
        from fastapi import FastAPI
        from fastapi.responses import PlainTextResponse

        _raw_app = FastAPI(title="SENTINEL Startup Diagnostics")

        @_raw_app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        async def _handle_startup_error(full_path: str):
            return PlainTextResponse(f"SENTINEL STARTUP ERROR:\n{_tb}", status_code=500)


class VercelPathCorrectionMiddleware:
    """
    ASGI middleware ensuring that requests rewritten by Vercel's edge network
    are cleanly dispatched to FastAPI routes regardless of rewrite translation.
    - If Vercel passes x-matched-path (or x-vercel-matched-path, x-forwarded-uri),
      restores the intended original path in scope['path'].
    - If path is /api/index.py or /api/index (or trailing slash), maps to root '/'
      if no matched header is present.
    """
    def __init__(self, inner_app):
        self.inner_app = inner_app

    def __getattr__(self, name):
        return getattr(self.inner_app, name)

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            headers = dict(scope.get("headers", []))

            # Check if Vercel passed the original matched path header
            matched_header = (
                headers.get(b"x-matched-path")
                or headers.get(b"x-vercel-matched-path")
                or headers.get(b"x-forwarded-uri")
                or headers.get(b"x-original-uri")
            )
            if matched_header:
                orig_path = matched_header.decode("latin1", errors="replace").split("?")[0]
                if orig_path and orig_path != path:
                    scope["path"] = orig_path
            elif path in ("/api/index.py", "/api/index", "/api/index.py/", "/api/index/", "/index.py", "/index"):
                scope["path"] = "/"

        await self.inner_app(scope, receive, send)


app = VercelPathCorrectionMiddleware(_raw_app)

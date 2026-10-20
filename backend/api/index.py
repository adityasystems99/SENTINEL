import os
import sys

# Ensure backend directory has top priority in sys.path for serverless execution
_current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/api
_backend_dir = os.path.dirname(_current_dir)              # backend
_repo_root = os.path.dirname(_backend_dir)                # repo root

# Add repo root to end if present, but place backend_dir strictly at index 0
# so backend packages (like backend/app and backend/demo_app) take precedence over any root app.py
if os.path.exists(_repo_root) and _repo_root not in sys.path:
    sys.path.append(_repo_root)

if os.path.exists(_backend_dir):
    if _backend_dir in sys.path:
        sys.path.remove(_backend_dir)
    sys.path.insert(0, _backend_dir)

try:
    from app.main import app
except (ImportError, AttributeError):
    from backend.app.main import app

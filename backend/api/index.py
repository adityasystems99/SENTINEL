import os
import sys

# Ensure backend directory is in sys.path for serverless execution
_current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/api
_backend_dir = os.path.dirname(_current_dir)              # backend
_repo_root = os.path.dirname(_backend_dir)                # repo root

for _p in [_backend_dir, _repo_root]:
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.main import app

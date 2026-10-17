"""Local filesystem store for project metadata and isolated workspaces.
Stores metadata.json separately from source files. Strictly no SQLite.
"""
import json
import os
import shutil
import threading
from typing import Dict, List, Optional
from ..config import settings
from ..models.project import ProjectMetadata, ProjectStatus

class ProjectStore:
    def __init__(self, base_dir: Optional[str] = None):
        self._lock = threading.RLock()
        self.base_dir = base_dir or settings.projects_dir
        self._projects_cache: Dict[str, ProjectMetadata] = {}
        self._init_storage()

    def _init_storage(self):
        """Ensure base directory exists and load existing metadata."""
        os.makedirs(self.base_dir, exist_ok=True)
        # Load existing projects on startup
        for entry in os.listdir(self.base_dir):
            proj_dir = os.path.join(self.base_dir, entry)
            meta_path = os.path.join(proj_dir, "metadata.json")
            if os.path.isdir(proj_dir) and os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        meta = ProjectMetadata(**data)
                        self._projects_cache[meta.project_id] = meta
                except Exception:
                    pass

    def get_project_dir(self, project_id: str) -> str:
        return os.path.join(self.base_dir, project_id)

    def get_source_dir(self, project_id: str) -> str:
        return os.path.join(self.base_dir, project_id, "source")

    def save_project(self, metadata: ProjectMetadata) -> None:
        """Save project metadata to memory and disk in metadata.json."""
        with self._lock:
            proj_dir = self.get_project_dir(metadata.project_id)
            os.makedirs(proj_dir, exist_ok=True)
            meta_path = os.path.join(proj_dir, "metadata.json")

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata.model_dump(), f, indent=2)

            self._projects_cache[metadata.project_id] = metadata

    def get_project(self, project_id: str) -> Optional[ProjectMetadata]:
        with self._lock:
            # Check cache first
            if project_id in self._projects_cache:
                return self._projects_cache[project_id]
            
            # Check disk
            meta_path = os.path.join(self.get_project_dir(project_id), "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = ProjectMetadata(**json.load(f))
                        self._projects_cache[project_id] = meta
                        return meta
                except Exception:
                    return None
            return None

    def list_projects(self) -> List[ProjectMetadata]:
        with self._lock:
            return list(self._projects_cache.values())

    def delete_project(self, project_id: str) -> bool:
        """Delete project workspace and metadata."""
        with self._lock:
            if project_id in self._projects_cache:
                del self._projects_cache[project_id]
            
            proj_dir = self.get_project_dir(project_id)
            if os.path.exists(proj_dir):
                shutil.rmtree(proj_dir, ignore_errors=True)
                return True
            return False

    def clear(self) -> None:
        """Clear all projects (useful for test resets)."""
        with self._lock:
            self._projects_cache.clear()
            if os.path.exists(self.base_dir):
                shutil.rmtree(self.base_dir, ignore_errors=True)
                os.makedirs(self.base_dir, exist_ok=True)

    def get_compatibility_path(self, project_id: str) -> str:
        return os.path.join(self.get_project_dir(project_id), "compatibility_report.json")

    def save_compatibility_report(self, project_id: str, report_data: dict) -> None:
        with self._lock:
            proj_dir = self.get_project_dir(project_id)
            os.makedirs(proj_dir, exist_ok=True)
            report_path = self.get_compatibility_path(project_id)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)

    def get_compatibility_report(self, project_id: str) -> Optional[dict]:
        with self._lock:
            report_path = self.get_compatibility_path(project_id)
            if os.path.exists(report_path):
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    return None
            return None

    def get_audit_path(self, project_id: str) -> str:
        return os.path.join(self.get_project_dir(project_id), "audit_report.json")

    def save_audit_report(self, project_id: str, report_data: dict) -> None:
        with self._lock:
            proj_dir = self.get_project_dir(project_id)
            os.makedirs(proj_dir, exist_ok=True)
            report_path = self.get_audit_path(project_id)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)

    def get_audit_report(self, project_id: str) -> Optional[dict]:
        with self._lock:
            report_path = self.get_audit_path(project_id)
            if os.path.exists(report_path):
                try:
                    with open(report_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    return None
            return None

project_store = ProjectStore()


"""Secure project ingestion service.
Handles validation, path traversal defense, resource bounds, and safe isolation.
"""
import fnmatch
import io
import os
import shutil
import zipfile
from typing import Dict, List, Tuple
from ..config import settings

def is_pattern_matched(filename: str, patterns: List[str]) -> bool:
    """Check if a filename or path matches any exclusion patterns."""
    # Normalize path separators
    normalized = filename.replace("\\", "/").strip("/")
    parts = normalized.split("/")

    for pattern in patterns:
        clean_pat = pattern.strip("/")
        # Check if any segment of the path matches (e.g. node_modules)
        for part in parts:
            if fnmatch.fnmatch(part.lower(), clean_pat.lower()):
                return True
        # Check full path
        if fnmatch.fnmatch(normalized.lower(), clean_pat.lower()):
            return True
        # Check basename
        if fnmatch.fnmatch(os.path.basename(normalized).lower(), clean_pat.lower()):
            return True
    return False

def validate_archive(file_bytes: bytes, filename: str) -> None:
    """Validate archive upload size, format, and magic bytes."""
    # 1. Extension check
    if not filename.lower().endswith(".zip"):
        raise ValueError("Invalid file type: only .zip archives are supported")

    # 2. Upload size check
    if len(file_bytes) == 0:
        raise ValueError("Archive file cannot be empty")

    if len(file_bytes) > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes // (1024 * 1024)
        raise ValueError(f"Archive exceeds maximum upload size limit ({max_mb} MB)")

    # 3. Magic number / ZIP structure check
    if not (file_bytes.startswith(b"PK\x03\x04") or file_bytes.startswith(b"PK\x05\x06") or file_bytes.startswith(b"PK\x07\x08")):
        raise ValueError("Corrupt or invalid ZIP archive header")

    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as z:
            # Test archive integrity
            first_bad = z.testzip()
            if first_bad is not None:
                raise ValueError(f"Corrupt ZIP archive: CRC error on entry '{first_bad}'")
    except zipfile.BadZipFile as e:
        raise ValueError(f"Corrupt or invalid ZIP archive: {str(e)}")

def inspect_frameworks(extracted_dir: str) -> List[str]:
    """Detect technologies and frameworks from extracted manifest files."""
    frameworks = []
    
    # Check for Python
    has_py = False
    for root, _, files in os.walk(extracted_dir):
        for f in files:
            if f in ("requirements.txt", "pyproject.toml", "setup.py", "Pipfile"):
                has_py = True
                frameworks.append("Python")
                # Inspect for FastAPI / Flask / Django
                try:
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as manifest:
                        content = manifest.read().lower()
                        if "fastapi" in content and "FastAPI" not in frameworks:
                            frameworks.append("FastAPI")
                        if "flask" in content and "Flask" not in frameworks:
                            frameworks.append("Flask")
                        if "django" in content and "Django" not in frameworks:
                            frameworks.append("Django")
                except Exception:
                    pass
                break
        if has_py:
            break

    # Check for Node.js / JavaScript / TypeScript
    pkg_path = None
    for root, _, files in os.walk(extracted_dir):
        if "package.json" in files:
            pkg_path = os.path.join(root, "package.json")
            if "Node.js" not in frameworks:
                frameworks.append("Node.js")
            break

    if pkg_path:
        try:
            with open(pkg_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                if "react" in content and "React" not in frameworks:
                    frameworks.append("React")
                if "vite" in content and "Vite" not in frameworks:
                    frameworks.append("Vite")
                if "next" in content and "Next.js" not in frameworks:
                    frameworks.append("Next.js")
                if "typescript" in content and "TypeScript" not in frameworks:
                    frameworks.append("TypeScript")
        except Exception:
            pass

    # Check for Docker
    for root, _, files in os.walk(extracted_dir):
        if "Dockerfile" in files or "docker-compose.yml" in files:
            frameworks.append("Docker")
            break

    return sorted(list(set(frameworks)))

def extract_archive_safely(file_bytes: bytes, target_dir: str) -> Dict:
    """Safely extract ZIP entries with strict path traversal, symlink, and resource checks."""
    os.makedirs(target_dir, exist_ok=True)
    canonical_target = os.path.normpath(os.path.abspath(target_dir))

    with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as z:
        entries = z.infolist()

        # 1. Archive entries count limit
        if len(entries) > settings.max_archive_entries:
            raise ValueError(f"Archive exceeds maximum entries limit ({settings.max_archive_entries})")

        # 2. Cumulative uncompressed size check
        total_uncompressed = sum(e.file_size for e in entries)
        if total_uncompressed > settings.max_extracted_size_bytes:
            max_mb = settings.max_extracted_size_bytes // (1024 * 1024)
            raise ValueError(f"Uncompressed archive size ({total_uncompressed // (1024*1024)} MB) exceeds limit ({max_mb} MB)")

        file_count = 0
        dir_count = 0
        excluded_count = 0
        extracted_bytes = 0
        sample_files = []

        # 3. First pass: Validate ALL entries before writing anything
        for entry in entries:
            name = entry.filename

            # Path traversal check
            if name.startswith("/") or name.startswith("\\") or ":" in name:
                raise ValueError(f"Security error: Absolute or illegal path in archive entry '{name}'")

            destination = os.path.normpath(os.path.abspath(os.path.join(canonical_target, name)))
            if os.path.commonpath([canonical_target, destination]) != canonical_target:
                raise ValueError(f"Security error: Path traversal detected in archive entry '{name}'")

            # Symlink check
            if (entry.external_attr >> 16) & 0o120000 == 0o120000:
                raise ValueError(f"Security error: Symlinks are prohibited in project archive ('{name}')")

            # Prohibited executable / binary check
            _, ext = os.path.splitext(name.lower())
            if ext in settings.prohibited_extensions:
                raise ValueError(f"Security error: Prohibited executable binary entry '{name}' detected. SENTINEL only analyzes source code repositories; compiled binaries ({', '.join(settings.prohibited_extensions)}) are prohibited.")

        # 4. Second pass: Extract non-excluded entries
        for entry in entries:
            name = entry.filename
            destination = os.path.normpath(os.path.abspath(os.path.join(canonical_target, name)))

            # Check exclusion policy
            if is_pattern_matched(name, settings.excluded_patterns):
                excluded_count += 1
                continue

            if entry.is_dir():
                os.makedirs(destination, exist_ok=True)
                dir_count += 1
            else:
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                with z.open(entry) as src, open(destination, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                file_count += 1
                extracted_bytes += entry.file_size
                rel_path = os.path.relpath(destination, canonical_target).replace("\\", "/")
                if len(sample_files) < 30:
                    sample_files.append(rel_path)

    # Detect frameworks from safely extracted files
    detected_frameworks = inspect_frameworks(canonical_target)

    return {
        "file_count": file_count,
        "directory_count": dir_count,
        "extracted_size_bytes": extracted_bytes,
        "excluded_items_count": excluded_count,
        "detected_frameworks": detected_frameworks,
        "sample_files": sample_files,
    }

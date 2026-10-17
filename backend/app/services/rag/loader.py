"""Knowledge document discovery, parsing, and text splitting for SENTINEL RAG."""
import hashlib
import os
import re
import time
from typing import Dict, List, Optional, Tuple

from ...models.rag import KnowledgeCategory, KnowledgeDocument

class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        title: str,
        source_path: str,
        category: KnowledgeCategory,
        affected_service: Optional[str],
        resolution_status: Optional[str],
        content: str,
        chunk_index: int,
    ):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.title = title
        self.source_path = source_path
        self.category = category
        self.affected_service = affected_service
        self.resolution_status = resolution_status
        self.content = content
        self.chunk_index = chunk_index
        self.fingerprint = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

def parse_markdown_metadata(raw_text: str) -> Dict[str, str]:
    """Extract metadata lines from markdown front sections (e.g. **Document ID:** INC-123)."""
    metadata: Dict[str, str] = {}
    lines = raw_text.splitlines()

    for line in lines[:20]:
        clean = line.strip().replace("*", "")
        if ":" in clean:
            key, val = clean.split(":", 1)
            key_clean = key.strip().lower().replace(" ", "_")
            metadata[key_clean] = val.strip()

    return metadata

def split_document_into_chunks(
    doc_id: str,
    title: str,
    source_path: str,
    category: KnowledgeCategory,
    affected_service: Optional[str],
    resolution_status: Optional[str],
    raw_content: str,
    max_chunk_chars: int = 800,
) -> List[DocumentChunk]:
    """Split markdown document into semantic section chunks based on headers and paragraphs."""
    chunks: List[DocumentChunk] = []

    # Split by markdown headers (## Section)
    sections = re.split(r'(?m)^(?=##\s+)', raw_content)
    chunk_idx = 0

    for sec in sections:
        sec_clean = sec.strip()
        if not sec_clean:
            continue

        # If section is small enough, keep as single chunk
        if len(sec_clean) <= max_chunk_chars:
            chunks.append(DocumentChunk(
                chunk_id=f"{doc_id}-chunk-{chunk_idx}",
                doc_id=doc_id,
                title=title,
                source_path=source_path,
                category=category,
                affected_service=affected_service,
                resolution_status=resolution_status,
                content=sec_clean,
                chunk_index=chunk_idx,
            ))
            chunk_idx += 1
        else:
            # Further split by double newlines (paragraphs)
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', sec_clean) if p.strip()]
            current_buffer = []
            current_len = 0

            for p in paragraphs:
                if current_len + len(p) > max_chunk_chars and current_buffer:
                    chunk_text = "\n\n".join(current_buffer)
                    chunks.append(DocumentChunk(
                        chunk_id=f"{doc_id}-chunk-{chunk_idx}",
                        doc_id=doc_id,
                        title=title,
                        source_path=source_path,
                        category=category,
                        affected_service=affected_service,
                        resolution_status=resolution_status,
                        content=chunk_text,
                        chunk_index=chunk_idx,
                    ))
                    chunk_idx += 1
                    current_buffer = [p]
                    current_len = len(p)
                else:
                    current_buffer.append(p)
                    current_len += len(p)

            if current_buffer:
                chunk_text = "\n\n".join(current_buffer)
                chunks.append(DocumentChunk(
                    chunk_id=f"{doc_id}-chunk-{chunk_idx}",
                    doc_id=doc_id,
                    title=title,
                    source_path=source_path,
                    category=category,
                    affected_service=affected_service,
                    resolution_status=resolution_status,
                    content=chunk_text,
                    chunk_index=chunk_idx,
                ))
                chunk_idx += 1

    return chunks

def load_knowledge_directory(base_dir: str) -> Tuple[List[KnowledgeDocument], List[DocumentChunk]]:
    """Scan knowledge directory, parse documents, and generate chunked index items."""
    docs: List[KnowledgeDocument] = []
    all_chunks: List[DocumentChunk] = []

    if not os.path.exists(base_dir):
        return docs, all_chunks

    for root, _, files in os.walk(base_dir):
        for f in files:
            if not f.endswith((".md", ".txt", ".json")):
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read()

                meta = parse_markdown_metadata(content)
                doc_id = meta.get("document_id") or meta.get("doc_id") or os.path.splitext(f)[0]

                # Extract title from first line # Title
                first_line = content.splitlines()[0] if content.splitlines() else f
                title = first_line.lstrip("# ").strip() if first_line.startswith("#") else f

                # Determine category
                cat_raw = meta.get("category", "").lower()
                if "runbook" in cat_raw or "runbook" in f.lower():
                    category = KnowledgeCategory.TROUBLESHOOTING_RUNBOOK
                elif "scenario" in cat_raw:
                    category = KnowledgeCategory.FAILURE_SCENARIO
                else:
                    category = KnowledgeCategory.INCIDENT_POSTMORTEM

                affected_svc = meta.get("affected_service")
                resolution_status = meta.get("resolution_status", "RESOLVED")

                chunks = split_document_into_chunks(
                    doc_id=doc_id,
                    title=title,
                    source_path=rel_path,
                    category=category,
                    affected_service=affected_svc,
                    resolution_status=resolution_status,
                    raw_content=content,
                )

                docs.append(KnowledgeDocument(
                    doc_id=doc_id,
                    title=title,
                    source_path=rel_path,
                    category=category,
                    affected_service=affected_svc,
                    resolution_status=resolution_status,
                    timestamp=time.time(),
                    content=content,
                    chunk_count=len(chunks),
                ))

                all_chunks.extend(chunks)

            except Exception as e:
                print(f"Error reading knowledge document {full_path}: {e}")

    return docs, all_chunks

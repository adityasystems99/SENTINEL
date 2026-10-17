"""API routes for Phase 6: RAG Historical Incident Intelligence."""
import os
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from ..config import settings
from ..models.rag import (
    KnowledgeDocument,
    RAGIngestResult,
    RAGQuery,
    RetrievedChunk,
)
from ..services.rag import (
    initialize_knowledge_base,
    load_knowledge_directory,
    vector_store,
)
from ..auth.security import UserContext, get_current_user
from ..auth.rate_limiter import check_rate_limit

router = APIRouter(prefix="/rag", tags=["RAG Historical Intelligence"])

@router.get("/documents", response_model=List[KnowledgeDocument])
async def list_knowledge_documents(current_user: UserContext = Depends(get_current_user)):
    """List all discoverable knowledge documents in the version-controlled collection."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    knowledge_dir = os.path.join(repo_root, "backend", "knowledge")
    docs, _ = load_knowledge_directory(knowledge_dir)
    return docs

@router.post(
    "/ingest",
    response_model=RAGIngestResult,
    dependencies=[Depends(check_rate_limit(max_requests=settings.expensive_rate_limit_per_minute, route_scope="rag_ingest"))],
)
async def ingest_knowledge_collection(current_user: UserContext = Depends(get_current_user)):
    """Trigger ingestion, parsing, chunking, and embedding of the knowledge base."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    knowledge_dir = os.path.join(repo_root, "backend", "knowledge")

    docs, chunks = load_knowledge_directory(knowledge_dir)
    vector_store.clear()
    indexed_count = vector_store.add_chunks(chunks)

    total_tokens = sum(len(c.content.split()) for c in chunks)
    sources = list(set(c.source_path for c in chunks))

    return RAGIngestResult(
        documents_discovered=len(docs),
        chunks_indexed=indexed_count,
        total_tokens=total_tokens,
        sources=sources,
        ingested_at=time.time(),
    )

@router.post("/query", response_model=List[RetrievedChunk])
async def query_rag_engine(req: RAGQuery, current_user: UserContext = Depends(get_current_user)):
    """Perform hybrid similarity search across indexed historical incidents and runbooks."""
    if not req.query_text or not req.query_text.strip():
        raise HTTPException(status_code=400, detail="query_text must not be empty")

    # If vector store is empty, auto-initialize
    if vector_store.total_chunks == 0:
        initialize_knowledge_base()

    return vector_store.search(
        query=req.query_text,
        top_k=req.top_k,
        affected_service=req.affected_service,
    )

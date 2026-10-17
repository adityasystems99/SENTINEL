"""Lightweight in-memory vector store and hybrid retrieval engine for SENTINEL RAG.
Computes deterministic semantic embeddings and BM25 keyword overlap without external database requirements.
Adheres strictly to zero-SQLite and zero-external-vector-DB constraints.
"""
import hashlib
import json
import math
import os
import re
from typing import Dict, List, Optional, Set, Tuple

from ...models.rag import RetrievedChunk
from .loader import DocumentChunk, load_knowledge_directory

EMBEDDING_DIM = 64

def tokenize(text: str) -> List[str]:
    """Extract lowercased alphanumeric tokens from text."""
    return re.findall(r'[a-zA-Z0-9_\-\.]+', text.lower())

def compute_semantic_vector(text: str) -> List[float]:
    """Generate a deterministic normalized 64-dimensional dense semantic embedding using term-frequency hashing."""
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * EMBEDDING_DIM

    vec = [0.0] * EMBEDDING_DIM

    for tok in tokens:
        # Generate hash buckets for token
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        bucket = h % EMBEDDING_DIM
        weight = 1.0 + (math.log(len(tok)) if len(tok) > 3 else 0.5)
        vec[bucket] += weight

        # Subword n-grams for technical tokens
        if len(tok) > 4:
            for i in range(len(tok) - 3):
                sub = tok[i:i+4]
                h_sub = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16)
                vec[h_sub % EMBEDDING_DIM] += 0.3

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0.0:
        vec = [x / norm for x in vec]

    return vec

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two unit vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, dot))

class IndexedChunk:
    def __init__(self, chunk: DocumentChunk, vector: List[float]):
        self.chunk = chunk
        self.vector = vector
        self.keywords = set(tokenize(chunk.title + " " + chunk.content))

class LocalVectorStore:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join("data", "knowledge", "vector_index.json")
        self._chunks: Dict[str, IndexedChunk] = {}
        self._dedup_hashes: Set[str] = set()

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Embed and index document chunks with deduplication."""
        added = 0
        for ch in chunks:
            if ch.fingerprint in self._dedup_hashes:
                continue

            vec = compute_semantic_vector(ch.title + " " + ch.content)
            idx_chunk = IndexedChunk(ch, vec)
            self._chunks[ch.chunk_id] = idx_chunk
            self._dedup_hashes.add(ch.fingerprint)
            added += 1

        return added

    def search(
        self,
        query: str,
        top_k: int = 4,
        affected_service: Optional[str] = None
    ) -> List[RetrievedChunk]:
        """Hybrid search combining keyword frequency, service affinity, and cosine vector similarity."""
        query_clean = query.strip()
        if not query_clean or not self._chunks:
            return []

        query_vec = compute_semantic_vector(query_clean)
        query_tokens = set(tokenize(query_clean))

        scored_results: List[Tuple[float, IndexedChunk, str]] = []

        for idx_chunk in self._chunks.values():
            ch = idx_chunk.chunk

            # 1. Vector cosine similarity
            cos_sim = cosine_similarity(query_vec, idx_chunk.vector)

            # 2. Keyword Jaccard / Overlap score
            overlap_count = len(query_tokens.intersection(idx_chunk.keywords))
            keyword_score = min(1.0, overlap_count / max(1, len(query_tokens))) if query_tokens else 0.0

            # 3. Service affinity bonus
            service_bonus = 0.0
            reasons = []

            if affected_service and ch.affected_service:
                if affected_service.lower() in ch.affected_service.lower() or ch.affected_service.lower() in affected_service.lower():
                    service_bonus = 0.15
                    reasons.append(f"Direct service match: [{ch.affected_service}]")

            if overlap_count >= 2:
                matching_words = list(query_tokens.intersection(idx_chunk.keywords))[:3]
                reasons.append(f"Keyword match on {', '.join(matching_words)}")

            # Hybrid score computation
            hybrid_score = round(min(1.0, (0.45 * cos_sim) + (0.40 * keyword_score) + service_bonus), 4)

            # Filter out random noise when no keywords and no service match
            if overlap_count == 0 and service_bonus == 0:
                if cos_sim < 0.45:
                    continue

            # Filter out near-zero noise
            if hybrid_score >= 0.25:
                reason_str = "; ".join(reasons) if reasons else f"Semantic similarity ({int(hybrid_score * 100)}%)"
                scored_results.append((hybrid_score, idx_chunk, reason_str))


        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x[0], reverse=True)

        retrieved: List[RetrievedChunk] = []
        for score, item, reason in scored_results[:top_k]:
            ch = item.chunk
            # Format clean excerpt
            excerpt_lines = ch.content.strip().splitlines()
            excerpt = "\n".join(excerpt_lines[:8])
            if len(excerpt_lines) > 8:
                excerpt += "\n..."

            retrieved.append(RetrievedChunk(
                chunk_id=ch.chunk_id,
                doc_id=ch.doc_id,
                title=ch.title,
                source_path=ch.source_path,
                category=ch.category.value if hasattr(ch.category, "value") else str(ch.category),
                affected_service=ch.affected_service,
                similarity_score=score,
                excerpt=excerpt,
                resolution_status=ch.resolution_status,
                relevance_reason=reason,
            ))

        return retrieved

    def clear(self):
        """Clear indexed chunks."""
        self._chunks.clear()
        self._dedup_hashes.clear()

    @property
    def total_chunks(self) -> int:
        return len(self._chunks)

# Global singleton vector store
vector_store = LocalVectorStore()

def initialize_knowledge_base(knowledge_dir: str = "backend/knowledge") -> int:
    """Discover and ingest the version-controlled sample knowledge base."""
    if not os.path.isabs(knowledge_dir):
        # Resolve relative to repo root (4 levels up from backend/app/services/rag/)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        candidate = os.path.join(repo_root, knowledge_dir)
        if os.path.exists(candidate):
            knowledge_dir = candidate
        else:
            # Fallback: check relative to backend directory (3 levels up)
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            cand2 = os.path.join(backend_dir, "knowledge")
            if os.path.exists(cand2):
                knowledge_dir = cand2
            elif os.path.exists(knowledge_dir):
                knowledge_dir = os.path.abspath(knowledge_dir)

    docs, chunks = load_knowledge_directory(knowledge_dir)
    indexed_count = vector_store.add_chunks(chunks)
    return indexed_count

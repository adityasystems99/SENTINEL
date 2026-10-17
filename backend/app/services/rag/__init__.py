"""RAG historical incident intelligence package."""
from .loader import load_knowledge_directory, split_document_into_chunks
from .vector_store import (
    LocalVectorStore,
    vector_store,
    initialize_knowledge_base,
    compute_semantic_vector,
    cosine_similarity,
)
from .synthesizer import synthesize_investigation

__all__ = [
    "load_knowledge_directory",
    "split_document_into_chunks",
    "LocalVectorStore",
    "vector_store",
    "initialize_knowledge_base",
    "compute_semantic_vector",
    "cosine_similarity",
    "synthesize_investigation",
]

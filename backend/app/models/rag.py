"""Data models for Phase 6: RAG-Powered Historical Incident Intelligence."""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class KnowledgeCategory(str, Enum):
    INCIDENT_POSTMORTEM = "incident_postmortem"
    TROUBLESHOOTING_RUNBOOK = "troubleshooting_runbook"
    ARCHITECTURE_DOC = "architecture_doc"
    FAILURE_SCENARIO = "failure_scenario"

class KnowledgeDocument(BaseModel):
    doc_id: str
    title: str
    source_path: str
    category: KnowledgeCategory
    affected_service: Optional[str] = None
    resolution_status: Optional[str] = None
    timestamp: Optional[float] = None
    content: str
    chunk_count: int = 1

class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    source_path: str
    category: str
    affected_service: Optional[str] = None
    similarity_score: float = Field(..., description="Hybrid BM25 + cosine similarity score between 0.0 and 1.0")
    excerpt: str
    resolution_status: Optional[str] = None
    relevance_reason: str

class RAGQuery(BaseModel):
    query_text: str
    affected_service: Optional[str] = None
    top_k: int = 4

class InvestigationSynthesis(BaseModel):
    observed_facts: List[str] = Field(..., description="Concrete facts proven by current telemetry and graph analysis")
    root_cause_hypotheses: List[str] = Field(..., description="Hypotheses ranked by the existing NetworkX ranking engine")
    historical_evidence: List[RetrievedChunk] = Field(default_factory=list, description="Relevant excerpts from past postmortems and runbooks")
    recommended_investigation: List[str] = Field(default_factory=list, description="Concrete diagnostic actions derived from runbooks")
    uncertainty_disclosures: List[str] = Field(default_factory=list, description="Missing telemetry signals, alternative possibilities, and limitations")
    synthesizer_mode: str = "deterministic_local"
    llm_synthesis: Optional[str] = None

class RAGIngestResult(BaseModel):
    documents_discovered: int
    chunks_indexed: int
    total_tokens: int
    sources: List[str]
    ingested_at: float

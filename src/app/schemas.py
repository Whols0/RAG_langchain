from typing import Any

from pydantic import BaseModel, Field


class IngestTextItem(BaseModel):
    text: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    items: list[IngestTextItem]


class IngestFileRequest(BaseModel):
    paths: list[str] = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    indexed_chunks: int
    sources: list[str]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    filter: dict[str, Any] | None = None
    use_cache: bool = True


class Citation(BaseModel):
    source: str
    chunk_id: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    preview: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    cached: bool = False


class HealthResponse(BaseModel):
    status: str
    checks: dict[str, str]

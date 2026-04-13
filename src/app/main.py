from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI

from app.config import Settings, get_settings
from app.logging import configure_logging
from app.rag.service import RAGService
from app.schemas import (
    HealthResponse,
    IngestFileRequest,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.rag_service = RAGService(settings)
    logger.info("app_started", env=settings.app_env)
    yield


app = FastAPI(title="Production RAG", version="0.1.0", lifespan=lifespan)


def get_rag_service() -> RAGService:
    return app.state.rag_service


@app.get("/healthz", response_model=HealthResponse)
def healthz(service: RAGService = Depends(get_rag_service)) -> HealthResponse:
    checks = service.healthcheck()
    status = "ok" if all(value == "ok" or value == "disabled" for value in checks.values()) else "degraded"
    return HealthResponse(status=status, checks=checks)


@app.post("/v1/ingest/text", response_model=IngestResponse)
def ingest_text(
    request: IngestRequest,
    service: RAGService = Depends(get_rag_service),
) -> IngestResponse:
    chunk_count = service.ingest_texts(request.items)
    return IngestResponse(indexed_chunks=chunk_count, sources=[item.source for item in request.items])


@app.post("/v1/ingest/file", response_model=IngestResponse)
def ingest_file(
    request: IngestFileRequest,
    service: RAGService = Depends(get_rag_service),
) -> IngestResponse:
    chunk_count = service.ingest_paths(request.paths, request.metadata)
    return IngestResponse(indexed_chunks=chunk_count, sources=request.paths)


@app.post("/v1/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    service: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    return service.answer(
        question=request.question,
        filter_data=request.filter,
        use_cache=request.use_cache,
    )

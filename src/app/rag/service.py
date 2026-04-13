import hashlib
from typing import Any

import orjson
import redis
import structlog
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from app.config import Settings
from app.rag.chunker import DocumentChunker
from app.rag.loaders import load_path
from app.rag.prompts import SYSTEM_PROMPT, build_context_prompt
from app.rag.vectorstore import build_vector_store
from app.schemas import Citation, IngestTextItem, QueryResponse

logger = structlog.get_logger(__name__)


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.chunker = DocumentChunker(settings)
        self.vector_store = build_vector_store(settings)
        self.llm = ChatOpenAI(
            model=settings.openai_chat_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.cache = self._build_cache()

    def ingest_texts(self, items: list[IngestTextItem]) -> int:
        docs = [
            Document(
                page_content=item.text,
                metadata={"source": item.source, **item.metadata},
            )
            for item in items
        ]
        chunks = self.chunker.split(docs)
        ids = [chunk.metadata["chunk_id"] for chunk in chunks]
        self.vector_store.add_documents(documents=chunks, ids=ids)
        logger.info("ingest_completed", chunk_count=len(chunks), sources=[item.source for item in items])
        return len(chunks)

    def ingest_paths(self, paths: list[str], metadata: dict[str, Any] | None = None) -> int:
        docs: list[Document] = []
        metadata = metadata or {}
        sources: list[str] = []

        for path in paths:
            loaded = load_path(path)
            for document in loaded:
                document.metadata = {
                    **document.metadata,
                    **metadata,
                    "source": document.metadata.get("source") or path,
                }
            docs.extend(loaded)
            sources.append(path)

        chunks = self.chunker.split(docs)
        ids = [chunk.metadata["chunk_id"] for chunk in chunks]
        self.vector_store.add_documents(documents=chunks, ids=ids)
        logger.info("file_ingest_completed", chunk_count=len(chunks), sources=sources)
        return len(chunks)

    def answer(self, question: str, filter_data: dict[str, Any] | None, use_cache: bool) -> QueryResponse:
        cache_key = self._cache_key(question=question, filter_data=filter_data)
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                payload = orjson.loads(cached)
                return QueryResponse(**payload, cached=True)

        docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
            query=question,
            k=self.settings.retrieval_k,
            filter=filter_data,
        )
        docs_with_scores = docs_with_scores[: self.settings.max_context_docs]
        context = self._build_context(docs_with_scores)

        messages = [
            ("system", SYSTEM_PROMPT),
            ("human", build_context_prompt(question=question, context=context)),
        ]
        answer = self.llm.invoke(messages).content
        response = QueryResponse(
            answer=answer,
            citations=self._build_citations(docs_with_scores),
            cached=False,
        )

        if use_cache and self.cache:
            self.cache.setex(
                cache_key,
                self.settings.redis_ttl_seconds,
                orjson.dumps(response.model_dump()),
            )
        return response

    def healthcheck(self) -> dict[str, str]:
        checks = {"postgres": "ok", "redis": "disabled"}

        try:
            self.vector_store.similarity_search("healthcheck", k=1)
        except Exception as exc:  # pragma: no cover
            logger.exception("postgres_healthcheck_failed", error=str(exc))
            checks["postgres"] = "error"

        if self.cache:
            try:
                self.cache.ping()
                checks["redis"] = "ok"
            except Exception as exc:  # pragma: no cover
                logger.exception("redis_healthcheck_failed", error=str(exc))
                checks["redis"] = "error"

        return checks

    def _build_context(self, docs_with_scores: list[tuple[Document, float]]) -> str:
        parts = []
        for document, score in docs_with_scores:
            source = document.metadata.get("source", "unknown")
            chunk_id = document.metadata.get("chunk_id", "unknown")
            parts.append(
                f"[source={source} chunk_id={chunk_id} score={score:.4f}]\n{document.page_content}"
            )
        return "\n\n".join(parts)

    def _build_citations(self, docs_with_scores: list[tuple[Document, float]]) -> list[Citation]:
        citations = []
        for document, score in docs_with_scores:
            text = document.page_content.strip().replace("\n", " ")
            citations.append(
                Citation(
                    source=str(document.metadata.get("source", "unknown")),
                    chunk_id=str(document.metadata.get("chunk_id", "unknown")),
                    score=score,
                    metadata=document.metadata,
                    preview=text[:240],
                )
            )
        return citations

    def _build_cache(self) -> redis.Redis | None:
        if not self.settings.enable_cache:
            return None
        return redis.Redis.from_url(self.settings.redis_url, decode_responses=False)

    @staticmethod
    def _cache_key(question: str, filter_data: dict[str, Any] | None) -> str:
        raw = orjson.dumps({"question": question, "filter": filter_data or {}})
        return "rag:" + hashlib.sha1(raw).hexdigest()

import hashlib

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import Settings


class DocumentChunker:
    def __init__(self, settings: Settings) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )

    def split(self, docs: list[Document]) -> list[Document]:
        chunks = self._splitter.split_documents(docs)
        for index, chunk in enumerate(chunks):
            source = str(chunk.metadata.get("source", "unknown"))
            chunk.metadata["chunk_id"] = self._build_chunk_id(source=source, index=index)
        return chunks

    @staticmethod
    def _build_chunk_id(source: str, index: int) -> str:
        digest = hashlib.sha1(f"{source}:{index}".encode("utf-8")).hexdigest()
        return digest

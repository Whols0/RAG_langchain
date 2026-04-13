from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from app.config import Settings


def build_embeddings(settings: Settings) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def build_vector_store(settings: Settings) -> PGVector:
    embeddings = build_embeddings(settings)
    return PGVector(
        embeddings=embeddings,
        collection_name=settings.pgvector_collection,
        connection=settings.postgres_connection_string,
        embedding_length=settings.embedding_dimension,
        use_jsonb=True,
        create_extension=True,
    )

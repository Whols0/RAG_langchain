from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="langchain-production-rag", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-large", alias="OPENAI_EMBEDDING_MODEL"
    )
    openai_temperature: float = Field(default=0.0, alias="OPENAI_TEMPERATURE")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="rag", alias="POSTGRES_DB")
    postgres_user: str = Field(default="rag", alias="POSTGRES_USER")
    postgres_password: str = Field(default="rag", alias="POSTGRES_PASSWORD")
    pgvector_collection: str = Field(default="knowledge_base", alias="PGVECTOR_COLLECTION")
    embedding_dimension: int = Field(default=3072, alias="EMBEDDING_DIMENSION")

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_ttl_seconds: int = Field(default=600, alias="REDIS_TTL_SECONDS")
    enable_cache: bool = Field(default=True, alias="ENABLE_CACHE")

    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")
    retrieval_k: int = Field(default=6, alias="RETRIEVAL_K")
    retrieval_fetch_k: int = Field(default=24, alias="RETRIEVAL_FETCH_K")
    max_context_docs: int = Field(default=6, alias="MAX_CONTEXT_DOCS")

    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="production-rag", alias="LANGSMITH_PROJECT")

    @property
    def postgres_connection_string(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

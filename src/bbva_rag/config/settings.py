"""Configuración central"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- APP---
    app_env: Literal["dev", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    data_dir: Path = PROJECT_ROOT / "data"

    # --- Scraping ---
    scrape_sitemap_url: str = "https://www.bancolombia.com/sitemap-index.xml"
    scrape_allowed_domains: list[str] = ["www.bancolombia.com", "valores.bancolombia.com"]
    scrape_exclude_patterns: list[str] = [
        "simulador",
        "llamanos",
        "chatea-con-nosotros",
        "-viejo",
        "historias-que-transforman",
        "/src/",
    ]
    scrape_soft404_paths: list[str] = ["/personas"]
    scrape_user_agent: str = (
        "Mozilla/5.0 (compatible; bbva-rag-assistant/0.1; "
        "+https://github.com/SergioANJ/bbva-rag-assistant)"
    )
    scrape_download_delay: float = Field(default=1.5, ge=0.5)
    scrape_max_pages: int = Field(default=0, ge=0)  # 0 = no limit
    scrape_http_cache: bool = True

    # --- Cleaning ---
    clean_boilerplate_min_doc_freq: float = Field(default=0.10, gt=0.0, le=1.0)
    clean_min_chars: int = Field(default=200, ge=0)

    # --- Chunking ---
    chunk_min_chars: int = Field(default=100, ge=0)
    chunk_size: int = Field(default=1000, gt=0)
    chunk_overlap: int = Field(default=150, ge=0)

    # --- OpenAI ---
    openai_api_key: SecretStr | None = None

    # --- Embeddings ---
    embedding_provider: Literal["openai"] = "openai"  # se pueden agregare + models
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = Field(default=1536, gt=0)
    embedding_batch_size: int = Field(default=100, gt=0, le=2048)
    sparse_model: str = "Qdrant/bm25"
    sparse_language: str = "spanish"

    # --- Vector store (Qdrant) ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "bancolombia_chunks"

    # --- Retrieval ---
    retrieval_strategy: Literal["semantic", "bm25", "hybrid"] = "hybrid"
    retrieval_top_k: int = Field(default=15, gt=0)

    # --- Reranker ---
    reranker_enabled: bool = True
    reranker_model: str = "jinaai/jina-reranker-v2-base-multilingual"
    rerank_top_n: int = Field(default=5, gt=0)
    relevance_threshold: float = 0.0
    max_query_rewrites: int = Field(default=1, ge=0)

    # --- Local model cache (FastEmbed) ---
    models_cache_dir: Path = PROJECT_ROOT / ".cache" / "models"

    # --- LLM ---
    llm_provider: Literal["openai"] = "openai"
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=800, gt=0)
    llm_timeout_seconds: float = Field(default=30.0, gt=0)

    # --- Conversation memory ---
    history_max_messages: int = Field(default=6, ge=0)

    # --- PostgreSQL (conversation history) ---
    postgres_host: str = "localhost"
    postgres_port: int = 55432
    postgres_user: str = "rag"
    postgres_password: SecretStr = SecretStr("rag")
    postgres_db: str = "rag_assistant"

    # --- API / UI ---
    api_base_url: str = "http://localhost:8000"

    @property
    def database_url(self) -> str:
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+psycopg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @model_validator(mode="after")
    def _validate_chunking(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.chunk_min_chars >= self.chunk_size:
            raise ValueError("CHUNK_MIN_CHARS must be smaller than CHUNK_SIZE")
        if self.rerank_top_n > self.retrieval_top_k:
            raise ValueError("RERANK_TOP_N cannot exceed RETRIEVAL_TOP_K")
        return self


@lru_cache
def get_settings() -> Settings:
    """Singleton accessor: settings are loaded and validated once per process."""
    return Settings()

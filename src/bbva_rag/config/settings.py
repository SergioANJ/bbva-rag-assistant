"""Configuración central"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
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


@lru_cache
def get_settings() -> Settings:
    """Singleton accessor: settings are loaded and validated once per process."""
    return Settings()

import pytest
from pydantic import ValidationError

from bbva_rag.config.settings import Settings


def test_defaults_load():
    settings = Settings(_env_file=None)
    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"


def test_env_override(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    assert Settings(_env_file=None).log_level == "DEBUG"


def test_invalid_log_level_raises(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "hola")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_overlap_must_be_smaller_than_chunk_size(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "100")
    monkeypatch.setenv("CHUNK_OVERLAP", "200")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)

"""Se construye el modelo de chat configurado."""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from bbva_rag.config import Settings


def create_chat_model(settings: Settings) -> BaseChatModel:
    if settings.llm_provider == "openai":
        if settings.openai_api_key is None:
            raise ValueError("OPENAI_API_KEY is required for the 'openai' LLM provider")
        return ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout_seconds,
            max_retries=3,
            api_key=settings.openai_api_key,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

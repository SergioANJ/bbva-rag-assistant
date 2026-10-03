"""Se construye el proveedor seleccionado """

from bbva_rag.config import Settings
from bbva_rag.embeddings.base import Embedder
from bbva_rag.embeddings.openai_embedder import OpenAIEmbedder

def create_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "openai":
        if settings.openai_api_key is None:
            raise ValueError("OPENAI_API_KEY is required for the 'openai' embedding provider")
        return OpenAIEmbedder(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            batch_size=settings.embedding_batch_size,
        )
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")

"""Enviar el texto a OpenAI t recibir los vectores #"""
from openai import OpenAI

class OpenAIEmbedder:
    def __init__(
        self,
        api_key: str,
        model: str,
        dimensions: int,
        batch_size: int = 100,
        client: OpenAI | None = None,
    ):
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size
        self._client = client or OpenAI(api_key=api_key, max_retries=3, timeout=30)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = self._client.embeddings.create(
                model=self.model, input=batch, dimensions=self.dimensions
            )
            #Nos aseguramos que cada vector corresponda al texto enviado
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend(item.embedding for item in ordered)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
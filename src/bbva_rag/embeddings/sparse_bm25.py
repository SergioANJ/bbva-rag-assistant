"""Vectores de palabras clave dispersos (BM25) calculados localmente
con FastEmbed (ONNX, sin PyTorch)."""

from dataclasses import dataclass

from fastembed import SparseTextEmbedding


@dataclass
class SparseVector:
    indices: list[int]
    values: list[float]


class BM25Encoder:
    def __init__(self, model_name: str = "Qdrant/bm25", language: str = "spanish"):
        self._model = SparseTextEmbedding(model_name=model_name, language=language)

    def embed_documents(self, texts: list[str]) -> list[SparseVector]:
        return [
            SparseVector(e.indices.tolist(), e.values.tolist()) for e in self._model.embed(texts)
        ]

    def embed_query(self, text: str) -> SparseVector:
        next(iter(self._model.query_embed(text)))

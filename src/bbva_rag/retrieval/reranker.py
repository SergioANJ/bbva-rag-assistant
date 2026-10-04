"""Reordenamiento entre codificadores con FastEmbed (ONNX, sin PyTorch)"""

from dataclasses import replace

from fastembed.rerank.cross_encoder import TextCrossEncoder

from bbva_rag.retrieval.base import RetrievedChunk


class CrossEncoderReranker:
    def __init__(self, model_name: str, cache_dir: str | None = None, encoder=None):
        self.model_name = model_name
        self._encoder = encoder or TextCrossEncoder(model_name=model_name, cache_dir=cache_dir)

    def rerank(self, query: str, chunks: list[RetrievedChunk], top_n: int) -> list[RetrievedChunk]:
        """Califica cada par (pregunta, fragmento) y conserva los n mejores fragmentos"""
        if not chunks:
            return []
        scores = self._encoder.rerank(query, [chunk.text for chunk in chunks])
        ranked = sorted(zip(chunks, scores, strict=True), key=lambda pair: pair[1], reverse=True)
        return [replace(chunk, score=float(score)) for chunk, score in ranked[:top_n]]

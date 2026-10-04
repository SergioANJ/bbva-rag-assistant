"Estado compartido por cada nodo del grafo RAG."

import operator
from typing import Annotated, TypedDict

from bbva_rag.retrieval.base import RetrievedChunk


class RAGState(TypedDict, total=False):
    # Entrada
    question: str
    history: list[dict]
    # Análisis de pregunta
    intent: str
    standalone_question: str
    # Retrieval
    candidates: list[RetrievedChunk]
    context: list[RetrievedChunk]
    attempts: int
    # Salida
    answer: str
    sources: list[dict]
    """Cada nodo agrega su propio tiempo; el reductor fusiona
      los diccionarios en lugar de reemplazarlos"""
    timings: Annotated[dict[str, float], operator.or_]
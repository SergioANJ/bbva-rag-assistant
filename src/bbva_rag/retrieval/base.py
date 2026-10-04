"""Formato de resultados e interfaz comunes para 
   todas las estrategias de recuperación."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    url: str
    title: str
    section: str
    text: str
    score: float


class Retriever(Protocol):
    name: str

    def retrieve(self, query: str, limit: int) -> list[RetrievedChunk]: ...
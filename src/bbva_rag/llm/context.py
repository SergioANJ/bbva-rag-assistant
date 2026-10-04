"""Formatea los fragmentos recuperados y el historial para el LLM,
y extrae las fuentes que cita."""

import re

from bbva_rag.retrieval.base import RetrievedChunk

CITATION = re.compile(r"\[(\d+)\]")


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Toma los fragmentos de texto que encontró Qdrant
    y los organiza pegándoles una etiqueta numerada"""
    return "\n\n".join(
        f"[{number}] {chunk.title} ({chunk.url})\n{chunk.text}"
        for number, chunk in enumerate(chunks, start=1)
    )


def format_history(history: list[dict]) -> str:
    """Toma la mememoria de los msm anteriores y se convierte en un
    tipo guion que el LLm pueda leer facilmente"""
    if not history:
        return "(sin mensajes previos)"
    labels = {"user": "Usuario", "assistant": "Asistente"}
    return "\n".join(f"{labels[m['role']]}: {m['content']}" for m in history)


def cited_sources(answer: str, chunks: list[RetrievedChunk]) -> list[dict]:
    """Fuentes únicas (título + URL) citadas en la respuesta, en orden de aparición"""
    seen, sources = set(), []
    for match in CITATION.findall(answer):
        number = int(match)
        if 1 <= number <= len(chunks):
            chunk = chunks[number - 1]
            if chunk.url not in seen:
                seen.add(chunk.url)
                sources.append({"title": chunk.title, "url": chunk.url})
    return sources

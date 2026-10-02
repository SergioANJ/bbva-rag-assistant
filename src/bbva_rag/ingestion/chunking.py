"""Divide las páginas limpias en fragmentos para su incrustación y recuperación"""

import uuid

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

"""Asignamos un divisor compatible con Markdown, se prefiere cortar por encabezados,
 luego por párrafos y luego por líneas."""


def build_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter.from_language(
        Language.MARKDOWN, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )


# Genera una línea fija con el título y seccion de la página
def context_header(page: dict) -> str:
    return f"Fuente: {page['title']} ({page['section']})"


# Crea un identificador único utilizando UUID
def chunk_id(url: str, position: int) -> str:
    """Stable UUID: same page and position always produce the same id."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{url}#{position}"))


def chunk_page(page: dict, splitter: RecursiveCharacterTextSplitter) -> list[dict]:
    header = context_header(page)
    return [
        {
            "chunk_id": chunk_id(page["url"], position),
            "url": page["url"],
            "title": page["title"],
            "section": page["section"],
            "fetched_at": page["fetched_at"],
            "position": position,
            "char_count": len(piece),
            "text": f"{header}\n\n{piece}",
        }
        for position, piece in enumerate(splitter.split_text(page["text"]))
    ]

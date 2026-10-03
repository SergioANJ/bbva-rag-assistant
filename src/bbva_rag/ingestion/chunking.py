"""Divide las páginas limpias en fragmentos para su incrustación y recuperación"""

import uuid

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

"""Asignamos un divisor compatible con Markdown, se prefiere cortar por encabezados,
 luego por párrafos y luego por líneas."""


def build_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter.from_language(
        Language.MARKDOWN, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )


def merge_small_pieces(pieces: list[str], min_chars: int) -> list[str]:
    """Adjunte fragmentos más cortos que min_chars al siguiente
    (un encabezado pertenece a lo que sigue)."""
    merged, carry = [], ""
    for piece in pieces:
        if carry:
            piece = f"{carry}\n\n{piece}"
            carry = ""
        if len(piece) < min_chars:
            carry = piece
            continue
        merged.append(piece)
    if carry:
        if merged:
            merged[-1] = f"{merged[-1]}\n\n{carry}"
        else:
            merged.append(carry)
    return merged


def repeat_table_headers(pieces: list[str]) -> list[str]:
    """Si una pieza continúa una tabla cortada por la pieza anterior,
    anteponga la fila de encabezado de esa tabla."""
    result, open_header = [], None
    for piece in pieces:
        if open_header and piece.startswith("|"):
            piece = f"{open_header}\n{piece}"
        open_header, previous = None, ""
        for line in piece.split("\n"):
            if not line.startswith("|"):
                open_header = None
            elif not previous.startswith("|"):
                open_header = line
            previous = line
        result.append(piece)
    return result


# Genera una línea fija con el título y seccion de la página
def context_header(page: dict) -> str:
    return f"Fuente: {page['title']} ({page['section']})"


# Crea un identificador único utilizando UUID
def chunk_id(url: str, position: int) -> str:
    """Stable UUID: same page and position always produce the same id."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{url}#{position}"))


def chunk_page(
    page: dict, splitter: RecursiveCharacterTextSplitter, min_chars: int = 0
) -> list[dict]:
    header = context_header(page)
    pieces = splitter.split_text(page["text"])
    pieces = repeat_table_headers(merge_small_pieces(pieces, min_chars))
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
        for position, piece in enumerate(pieces)
    ]

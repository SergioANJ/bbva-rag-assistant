from bbva_rag.ingestion.chunking import (
    build_splitter,
    chunk_page,
    context_header,
    merge_small_pieces,
    repeat_table_headers,
)


def make_page(text: str) -> dict:
    return {
        "url": "https://x.com/cdt",
        "title": "CDT",
        "section": "personas",
        "fetched_at": "2026-10-02",
        "text": text,
    }


def body(chunk: dict, page: dict) -> str:
    """Chunk text without the context header."""
    return chunk["text"].removeprefix(context_header(page) + "\n\n")


def test_prefers_cutting_at_headings():
    page = make_page("## Beneficios\n\n" + "a " * 300 + "\n\n## Requisitos\n\n" + "b " * 300)
    chunks = chunk_page(page, build_splitter(800, 0))
    assert len(chunks) == 2
    assert body(chunks[0], page).startswith("## Beneficios")
    assert body(chunks[1], page).startswith("## Requisitos")


def test_merges_small_consecutive_sections():
    page = make_page("### Conocer productos\n\n### Obtener documentos\n\n### Seguridad")
    assert len(chunk_page(page, build_splitter(800, 0))) == 1


def test_every_chunk_has_the_context_header():
    page = make_page("Texto del CDT. " * 200)
    chunks = chunk_page(page, build_splitter(500, 50))
    assert len(chunks) > 1
    assert all(c["text"].startswith("Fuente: CDT (personas)") for c in chunks)


def test_chunk_ids_are_stable_and_unique():
    page = make_page("Texto del CDT. " * 200)
    first = [c["chunk_id"] for c in chunk_page(page, build_splitter(500, 50))]
    second = [c["chunk_id"] for c in chunk_page(page, build_splitter(500, 50))]
    assert first == second
    assert len(set(first)) == len(first)


def test_small_heading_is_attached_to_the_next_piece():
    pieces = ["#### Pasos", "1. Abre la app. " * 20]
    merged = merge_small_pieces(pieces, min_chars=100)
    assert len(merged) == 1
    assert merged[0].startswith("#### Pasos")


def test_small_last_piece_is_attached_to_the_previous_one():
    pieces = ["Contenido largo. " * 20, "Fin"]
    merged = merge_small_pieces(pieces, min_chars=100)
    assert len(merged) == 1
    assert merged[0].endswith("Fin")


def test_table_continuation_gets_its_header():
    pieces = ["Tarifas\n\n| Tarifa | Valor |\n| Retiro | $ 100 |", "| Consulta | $ 50 |"]
    result = repeat_table_headers(pieces)
    assert result[1] == "| Tarifa | Valor |\n| Consulta | $ 50 |"


def test_new_table_does_not_inherit_previous_header():
    pieces = [
        "| Tarifa | Valor |\n| Retiro | $ 100 |\n\nOtro texto",
        "| Plan | Precio |\n| Oro | $ 9 |",
    ]
    result = repeat_table_headers(pieces)
    assert result[1] == pieces[1]

from bbva_rag.ingestion.chunking import build_splitter, chunk_page, context_header


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

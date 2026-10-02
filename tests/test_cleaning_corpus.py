from bbva_rag.cleaning.corpus import deduplicate, find_boilerplate_blocks, remove_blocks

FOOTER = "Para resolver inquietudes adicionales o recibir ayuda personalizada."


def test_finds_repeated_paragraphs_but_never_headings():
    texts = [f"## Beneficios\n\nContenido {i}\n\n{FOOTER}" for i in range(10)]
    assert find_boilerplate_blocks(texts, min_doc_freq=0.5) == {FOOTER}


def test_rare_blocks_are_not_boilerplate():
    texts = [f"{FOOTER}\n\nTexto {i}" for i in range(2)] + [f"Otro {i}" for i in range(18)]
    assert find_boilerplate_blocks(texts, min_doc_freq=0.5) == set()


def test_remove_blocks_keeps_content():
    assert (
        remove_blocks(f"## CDT\n\nInvierte seguro\n\n{FOOTER}", {FOOTER})
        == "## CDT\n\nInvierte seguro"
    )


def test_deduplicate_keeps_shortest_url():
    pages = [
        {"url": "https://x.com/personas/login", "content_hash": "abc"},
        {"url": "https://x.com/personas", "content_hash": "abc"},
    ]
    [kept] = deduplicate(pages)
    assert kept["url"] == "https://x.com/personas"
    assert kept["duplicate_urls"] == ["https://x.com/personas/login"]

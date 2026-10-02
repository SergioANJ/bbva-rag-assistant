"""Limpieza a nivel de corpus: bloques de texto repetitivos
 compartidos por muchas páginas y textos duplicados."""

import re
from collections import Counter

HEADING = re.compile(r"^#{1,6}\s+\S")


def split_blocks(text: str) -> list[str]:
    """Párrafos o encabezados separados por una línea en blanco."""
    return [block.strip() for block in text.split("\n\n") if block.strip()]


def is_heading(block: str) -> bool:
    return bool(HEADING.match(block)) and "\n" not in block


def find_boilerplate_blocks(texts: list[str], min_doc_freq: float) -> set[str]:
    """Bloques que no son encabezados y que aparecen en al menos `min_doc_freq` de los documentos"""
    doc_freq = Counter()
    for text in texts:
        doc_freq.update(set(split_blocks(text)))
    min_docs = max(2, int(min_doc_freq * len(texts)))
    return {
        block for block, count in doc_freq.items() if count >= min_docs and not is_heading(block)
    }


def remove_blocks(text: str, blocks: set[str]) -> str:
    return "\n\n".join(b for b in split_blocks(text) if b not in blocks)


def deduplicate(pages: list[dict]) -> list[dict]:
    """Conserva una página por cada texto distinto (la URL más corta) y anota las demás URL"""
    kept: dict[str, dict] = {}
    for page in sorted(pages, key=lambda p: len(p["url"])):
        existing = kept.get(page["content_hash"])
        if existing is None:
            kept[page["content_hash"]] = {**page, "duplicate_urls": []}
        else:
            existing["duplicate_urls"].append(page["url"])
    return list(kept.values())

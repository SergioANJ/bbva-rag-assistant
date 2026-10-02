"""Etapa de limpieza: HTML sin procesar -> páginas Markdown
 limpias en data/clean/pages.jsonl"""

import hashlib
import json
from statistics import median
from urllib.parse import urlsplit

from loguru import logger

from bbva_rag.cleaning.corpus import deduplicate, find_boilerplate_blocks, remove_blocks
from bbva_rag.cleaning.text import clean_page, extract_title
from bbva_rag.config import get_settings, setup_logging


def section_from_url(url: str) -> str:
    """Sección principal del sitio, utilizada posteriormente 
    como metadatos para filtrado y análisis"""
    parts = urlsplit(url)
    if parts.netloc.startswith("valores."):
        return "valores"
    return parts.path.strip("/").split("/")[0] or "home"


def load_pages(raw_dir) -> list[dict]:
    """Limpieza página por página de todo el código HTML sin
      procesar que aparece en el manifiesto"""
    with (raw_dir / "manifest.jsonl").open(encoding="utf-8") as manifest:
        records = [json.loads(line) for line in manifest]
    pages, seen_files = [], set()
    for record in records:
        if record["raw_path"] in seen_files:
            continue
        seen_files.add(record["raw_path"])
        html = (raw_dir / record["raw_path"]).read_text(encoding="utf-8")
        pages.append(
            {
                "url": record["url"],
                "title": extract_title(html),
                "section": section_from_url(record["url"]),
                "fetched_at": record["fetched_at"],
                "text": clean_page(html),
            }
        )
    return pages


def main() -> None:
    setup_logging()
    settings = get_settings()
    raw_dir, clean_dir = settings.data_dir / "raw", settings.data_dir / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)

    # 1. Limpieza pagina por pagina
    pages = load_pages(raw_dir)
    total = len(pages)

    # 2. Eliminar bloques de texto repetitivo compartidos por varias páginas.
    boilerplate = find_boilerplate_blocks(
        [p["text"] for p in pages], settings.clean_boilerplate_min_doc_freq
    )
    for page in pages:
        page["text"] = remove_blocks(page["text"], boilerplate)
        page["char_count"] = len(page["text"])
        page["content_hash"] = hashlib.sha256(page["text"].encode("utf-8")).hexdigest()[:16]

    # 3. Eliminar paginas sin suficiente contenido
    too_short = [p for p in pages if p["char_count"] < settings.clean_min_chars]
    pages = [p for p in pages if p["char_count"] >= settings.clean_min_chars]

    # 4. Combinar páginas con texto idéntico
    unique_pages = deduplicate(pages)

    with (clean_dir / "pages.jsonl").open("w", encoding="utf-8") as out:
        for page in unique_pages:
            out.write(json.dumps(page, ensure_ascii=False) + "\n")

    report = {
        "pages_in": total,
        "boilerplate_blocks_removed": sorted(boilerplate),
        "dropped_too_short": sorted(p["url"] for p in too_short),
        "duplicates_merged": len(pages) - len(unique_pages),
        "pages_out": len(unique_pages),
    }
    (clean_dir / "cleaning_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    sizes = [p["char_count"] for p in unique_pages]
    logger.info(f"Pages in: {total}")
    logger.info(f"Boilerplate blocks removed: {len(boilerplate)}")
    logger.info(f"Dropped (< {settings.clean_min_chars} chars): {len(too_short)}")
    logger.info(f"Duplicates merged: {report['duplicates_merged']}")
    logger.info(f"Pages out: {len(unique_pages)}")
    logger.info(
        f"Characters per page: min={min(sizes)} median={median(sizes):.0f} max={max(sizes)}"
    )


if __name__ == "__main__":
    main()

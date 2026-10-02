"""Cleaning stage: raw HTML -> clean Markdown pages in data/clean/pages.jsonl."""

import hashlib
import json
from statistics import median
from urllib.parse import urlsplit

from loguru import logger

from bbva_rag.cleaning.text import clean_page, extract_title
from bbva_rag.config import get_settings, setup_logging


def section_from_url(url: str) -> str:
    """Determina a qué sección del sitio web pertenece la página según su dirección URL"""
    parts = urlsplit(url)
    if parts.netloc.startswith("valores."):
        return "valores"
    return parts.path.strip("/").split("/")[0] or "home"


def main() -> None:
    setup_logging()
    data_dir = get_settings().data_dir
    raw_dir, clean_dir = data_dir / "raw", data_dir / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)

    with (raw_dir / "manifest.jsonl").open(encoding="utf-8") as manifest:
        records = [json.loads(line) for line in manifest]

    pages, seen_files = [], set()
    for record in records:
        if record["raw_path"] in seen_files:
            continue
        seen_files.add(record["raw_path"])

        html = (raw_dir / record["raw_path"]).read_text(encoding="utf-8")
        text = clean_page(html)
        pages.append(
            {
                "url": record["url"],
                "title": extract_title(html),
                "section": section_from_url(record["url"]),
                "fetched_at": record["fetched_at"],
                "char_count": len(text),
                "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
                "text": text,
            }
        )

    output = clean_dir / "pages.jsonl"
    with output.open("w", encoding="utf-8") as out:
        for page in pages:
            out.write(json.dumps(page, ensure_ascii=False) + "\n")

    sizes = [p["char_count"] for p in pages]
    logger.info(f"Pages cleaned: {len(pages)} (from {len(records)} manifest lines)")
    logger.info(
        f"Characters per page: min={min(sizes)} median={median(sizes):.0f} max={max(sizes)}"
    )
    logger.info(f"Empty pages: {sum(s == 0 for s in sizes)}")
    logger.info(f"Pages under 300 chars: {sum(s < 300 for s in sizes)}")
    logger.info(f"Distinct texts: {len({p['content_hash'] for p in pages})}")
    logger.info(f"Saved to {output}")


if __name__ == "__main__":
    main()

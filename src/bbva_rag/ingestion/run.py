"""Ingestion stage: clean pages -> chunks (embeddings and indexing come next)."""

import json
from collections import Counter
from statistics import median

from loguru import logger

from bbva_rag.config import get_settings, setup_logging
from bbva_rag.ingestion.chunking import build_splitter, chunk_page


def main() -> None:
    setup_logging()
    settings = get_settings()
    chunks_dir = settings.data_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    with (settings.data_dir / "clean" / "pages.jsonl").open(encoding="utf-8") as f:
        pages = [json.loads(line) for line in f]

    splitter = build_splitter(settings.chunk_size, settings.chunk_overlap)
    chunks = [chunk for page in pages for chunk in chunk_page(page, splitter)]

    with (chunks_dir / "chunks.jsonl").open("w", encoding="utf-8") as out:
        for chunk in chunks:
            out.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    sizes = [c["char_count"] for c in chunks]
    per_page = Counter(c["url"] for c in chunks)
    top_url, top_count = per_page.most_common(1)[0]
    logger.info(f"Pages: {len(pages)} -> chunks: {len(chunks)}")
    logger.info(f"Chunk size: min={min(sizes)} median={median(sizes):.0f} max={max(sizes)}")
    logger.info(f"Chunks under 100 chars: {sum(s < 100 for s in sizes)}")
    logger.info(
        f"Chunks per page: median={median(per_page.values()):.0f} max={top_count} ({top_url})"
    )


if __name__ == "__main__":
    main()

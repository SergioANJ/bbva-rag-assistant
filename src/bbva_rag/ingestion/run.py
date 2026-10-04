"""Etapa de ingesta: páginas limpias -> fragmentos -> vectores densos + BM25 -> Qdrant"""

import argparse
import json
import time
from collections import Counter
from statistics import median

from loguru import logger

from bbva_rag.config import Settings, get_settings, setup_logging
from bbva_rag.embeddings.factory import create_embedder
from bbva_rag.embeddings.sparse_bm25 import BM25Encoder
from bbva_rag.ingestion.chunking import build_splitter, chunk_page
from bbva_rag.retrieval.reranker import CrossEncoderReranker
from bbva_rag.vectorstore.qdrant_store import QdrantStore


def build_chunks(settings: Settings) -> list[dict]:
    chunks_dir = settings.data_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    with (settings.data_dir / "clean" / "pages.jsonl").open(encoding="utf-8") as f:
        pages = [json.loads(line) for line in f]

    splitter = build_splitter(settings.chunk_size, settings.chunk_overlap)
    chunks = [
        chunk for page in pages for chunk in chunk_page(page, splitter, settings.chunk_min_chars)
    ]

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
    return chunks


def index_chunks(settings: Settings, chunks: list[dict]) -> None:
    texts = [c["text"] for c in chunks]
    logger.info(f"Approximate tokens to embed: {sum(len(t) for t in texts) // 4:,}")

    started = time.perf_counter()
    dense = create_embedder(settings).embed_documents(texts)
    logger.info(f"Dense vectors: {len(dense)} in {time.perf_counter() - started:.1f}s")

    started = time.perf_counter()
    sparse = BM25Encoder(
        settings.sparse_model, settings.sparse_language, str(settings.models_cache_dir)
    ).embed_documents(texts)
    logger.info(f"BM25 vectors: {len(sparse)} in {time.perf_counter() - started:.1f}s")

    store = QdrantStore(settings.qdrant_url, settings.qdrant_collection)
    store.recreate_collection(settings.embedding_dimensions)
    store.upsert_chunks(chunks, dense, sparse)
    logger.info(f"Points in collection '{settings.qdrant_collection}': {store.count()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Chunk the clean corpus and index it in Qdrant.")
    parser.add_argument("--skip-index", action="store_true", help="only build chunks.jsonl")
    parser.add_argument(
        "--if-empty", action="store_true", help="skip indexing if the collection already has data"
    )
    parser.add_argument(
        "--download-models", action="store_true", help="download the reranker into the cache"
    )
    args = parser.parse_args()

    setup_logging()
    settings = get_settings()

    if args.skip_index:
        build_chunks(settings)
        return

    store = QdrantStore(settings.qdrant_url, settings.qdrant_collection)
    store.wait_until_ready()
    if args.if_empty and store.is_populated():
        logger.info(f"Collection '{settings.qdrant_collection}' already has data; skipping indexing")
    else:
        index_chunks(settings, build_chunks(settings))

    if args.download_models:
        logger.info(f"Downloading reranker {settings.reranker_model} (only the first time)")
        CrossEncoderReranker(settings.reranker_model, str(settings.models_cache_dir))
        logger.info("Models ready")


if __name__ == "__main__":
    main()

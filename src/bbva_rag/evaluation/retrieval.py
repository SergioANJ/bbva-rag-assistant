"""Evaluación de recuperación: compare las estrategias (y el reordenador)"""

import json
import time
from datetime import UTC, datetime
from statistics import mean

from loguru import logger

from bbva_rag.config import get_settings, setup_logging
from bbva_rag.config.settings import PROJECT_ROOT
from bbva_rag.embeddings.factory import create_embedder
from bbva_rag.embeddings.sparse_bm25 import BM25Encoder
from bbva_rag.evaluation.metrics import first_hit_rank, hit_rate, mean_reciprocal_rank
from bbva_rag.retrieval.base import RetrievedChunk
from bbva_rag.retrieval.factory import create_retriever
from bbva_rag.retrieval.reranker import CrossEncoderReranker
from bbva_rag.vectorstore.qdrant_store import QdrantStore

EVAL_DIR = PROJECT_ROOT / "eval"
STRATEGIES = ["semantic", "bm25", "hybrid"]
RERANKED = "hybrid+rerank"


def load_jsonl(path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def canonical_url_map(pages: list[dict]) -> dict[str, str]:
    """Asigna cada URL duplicada a la URL conservada durante la deduplicación"""
    mapping = {}
    for page in pages:
        mapping[page["url"]] = page["url"]
        for duplicate in page.get("duplicate_urls", []):
            mapping[duplicate] = page["url"]
    return mapping


def summarize(ranks: list[int | None], cutoffs: list[int]) -> dict:
    return {
        "ranks": ranks,
        **{f"hit@{k}": hit_rate(ranks, k) for k in cutoffs},
        "mrr": mean_reciprocal_rank(ranks),
    }


def main() -> None:
    setup_logging()
    settings = get_settings()
    cutoffs = sorted({1, 3, 5, settings.retrieval_top_k})
    cache_dir = str(settings.models_cache_dir)
    golden = load_jsonl(EVAL_DIR / "golden_set.jsonl")
    canonical = canonical_url_map(load_jsonl(settings.data_dir / "clean" / "pages.jsonl"))

    unknown = [
        (item["id"], url)
        for item in golden
        for url in item["expected_urls"]
        if url not in canonical
    ]
    if unknown:
        for question_id, url in unknown:
            logger.error(f"{question_id}: URL not in the clean corpus -> {url}")
        raise SystemExit("Fix the golden set URLs before running the evaluation.")

    def rank_of(chunks: list[RetrievedChunk], item: dict) -> int | None:
        urls = [canonical.get(chunk.url, chunk.url) for chunk in chunks]
        return first_hit_rank(urls, {canonical[url] for url in item["expected_urls"]})

    store = QdrantStore(settings.qdrant_url, settings.qdrant_collection)
    embedder = create_embedder(settings)
    bm25 = BM25Encoder(settings.sparse_model, settings.sparse_language, cache_dir)

    results, candidates = {}, {}
    for strategy in STRATEGIES:
        retriever = create_retriever(strategy, store, embedder, bm25)
        candidates[strategy] = [
            retriever.retrieve(item["question"], settings.retrieval_top_k) for item in golden
        ]
        results[strategy] = summarize(
            [
                rank_of(chunks, item)
                for chunks, item in zip(candidates[strategy], golden, strict=True)
            ],
            cutoffs,
        )

    if settings.reranker_enabled:
        logger.info(f"Loading reranker {settings.reranker_model} (first run downloads it)")
        reranker = CrossEncoderReranker(settings.reranker_model, cache_dir)
        ranks, seconds = [], []
        for chunks, item in zip(candidates["hybrid"], golden, strict=True):
            started = time.perf_counter()
            reranked = reranker.rerank(item["question"], chunks, top_n=len(chunks))
            seconds.append(time.perf_counter() - started)
            ranks.append(rank_of(reranked, item))
        results[RERANKED] = {**summarize(ranks, cutoffs), "avg_rerank_seconds": mean(seconds)}

    columns = list(results)
    print(f"\nPreguntas: {len(golden)}  |  candidatos por pregunta: {settings.retrieval_top_k}")
    if settings.reranker_enabled:
        print(
            f"Reranker: {settings.reranker_model}  |  "
            f"tiempo medio: {results[RERANKED]['avg_rerank_seconds']:.2f} s por pregunta"
        )
    print()
    print(f"{'Estrategia':14} " + " ".join(f"{f'hit@{k}':>7}" for k in cutoffs) + f" {'MRR':>6}")
    for name in columns:
        row = " ".join(f"{results[name][f'hit@{k}']:>7.0%}" for k in cutoffs)
        print(f"{name:14} {row} {results[name]['mrr']:>6.2f}")

    print("\nPosición de la página correcta por pregunta (- = no está en el top):")
    print(f"{'id':4} {'tipo':15} " + " ".join(f"{c:>13}" for c in columns) + "  pregunta")
    for i, item in enumerate(golden):
        positions = " ".join(f"{results[c]['ranks'][i] or '-':>13}" for c in columns)
        print(f"{item['id']:4} {item.get('type', ''):15} {positions}  {item['question'][:45]}")

    report = {
        "run_at": datetime.now(UTC).isoformat(),
        "config": {
            "embedding_model": settings.embedding_model,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "retrieval_top_k": settings.retrieval_top_k,
            "reranker_model": settings.reranker_model if settings.reranker_enabled else None,
        },
        "questions": len(golden),
        "results": results,
    }
    output = EVAL_DIR / "results" / "retrieval.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Report saved to {output}")


if __name__ == "__main__":
    main()

"""Retrieval evaluation: compare every strategy against the golden set."""

import json
from datetime import UTC, datetime

from loguru import logger

from bbva_rag.config import get_settings, setup_logging
from bbva_rag.config.settings import PROJECT_ROOT
from bbva_rag.embeddings.factory import create_embedder
from bbva_rag.embeddings.sparse_bm25 import BM25Encoder
from bbva_rag.evaluation.metrics import first_hit_rank, hit_rate, mean_reciprocal_rank
from bbva_rag.retrieval.factory import create_retriever
from bbva_rag.vectorstore.qdrant_store import QdrantStore

EVAL_DIR = PROJECT_ROOT / "eval"
STRATEGIES = ["semantic", "bm25", "hybrid"]
CUTOFFS = [1, 3, 5, 20]


def load_jsonl(path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def canonical_url_map(pages: list[dict]) -> dict[str, str]:
    """Asigna cada URL duplicada a la URL conservada durante la deduplicación."""
    mapping = {}
    for page in pages:
        mapping[page["url"]] = page["url"]
        for duplicate in page.get("duplicate_urls", []):
            mapping[duplicate] = page["url"]
    return mapping


def main() -> None:
    setup_logging()
    settings = get_settings()
    golden = load_jsonl(EVAL_DIR / "golden_set.jsonl")
    canonical = canonical_url_map(load_jsonl(settings.data_dir / "clean" / "pages.jsonl"))

    # Valida que este la URL antes de hacer llamado 
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

    store = QdrantStore(settings.qdrant_url, settings.qdrant_collection)
    embedder = create_embedder(settings)
    bm25 = BM25Encoder(settings.sparse_model, settings.sparse_language)

    results = {}
    for strategy in STRATEGIES:
        retriever = create_retriever(strategy, store, embedder, bm25)
        ranks = []
        for item in golden:
            chunks = retriever.retrieve(item["question"], settings.retrieval_top_k)
            urls = [canonical.get(chunk.url, chunk.url) for chunk in chunks]
            expected = {canonical[url] for url in item["expected_urls"]}
            ranks.append(first_hit_rank(urls, expected))
        results[strategy] = {
            "ranks": ranks,
            **{f"hit@{k}": hit_rate(ranks, k) for k in CUTOFFS},
            "mrr": mean_reciprocal_rank(ranks),
        }

    print(f"\nPreguntas: {len(golden)}  |  candidatos por pregunta: {settings.retrieval_top_k}\n")
    header = f"{'Estrategia':10} " + " ".join(f"{f'hit@{k}':>7}" for k in CUTOFFS) + f" {'MRR':>6}"
    print(header)
    for strategy, metrics in results.items():
        row = " ".join(f"{metrics[f'hit@{k}']:>7.0%}" for k in CUTOFFS)
        print(f"{strategy:10} {row} {metrics['mrr']:>6.2f}")

    print("\nPosición de la página correcta por pregunta (- = no está en el top):")
    print(f"{'id':4} {'tipo':15} " + " ".join(f"{s:>8}" for s in STRATEGIES) + "  pregunta")
    for i, item in enumerate(golden):
        positions = " ".join(f"{results[s]['ranks'][i] or '-':>8}" for s in STRATEGIES)
        print(f"{item['id']:4} {item.get('type', ''):15} {positions}  {item['question'][:50]}")

    report = {
        "run_at": datetime.now(UTC).isoformat(),
        "config": {
            "embedding_model": settings.embedding_model,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "retrieval_top_k": settings.retrieval_top_k,
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

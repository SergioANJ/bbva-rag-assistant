"""Calibrar el UMBRAL DE RELEVANCIA: mejor puntuación de reclasificación
para preguntas respondibles frente a preguntas no respondibles"""

import json

from loguru import logger

from bbva_rag.config import get_settings, setup_logging
from bbva_rag.evaluation.retrieval import EVAL_DIR, canonical_url_map, load_jsonl
from bbva_rag.graph.builder import RAGComponents, create_components
from bbva_rag.llm.prompts import analyze_messages
from bbva_rag.llm.schemas import QueryAnalysis

THRESHOLDS = [round(-0.6 + 0.1 * i, 1) for i in range(12)]  # -0.6 ... 0.5


def score_question(components: RAGComponents, settings, question: str) -> dict:
    """Ejecute los mismos pasos que en el gráfico hasta que el
    reordenador devuelva la mejor puntuación."""
    analysis = components.llm.with_structured_output(QueryAnalysis).invoke(
        analyze_messages(question, [])
    )
    if analysis.intent != "bank_query":
        return {"intent": analysis.intent, "score": None, "urls": []}
    candidates = components.retriever.retrieve(
        analysis.standalone_question, settings.retrieval_top_k
    )
    context = components.reranker.rerank(
        analysis.standalone_question, candidates, settings.rerank_top_n
    )
    return {
        "intent": analysis.intent,
        "score": context[0].score if context else None,
        "urls": [chunk.url for chunk in context],
    }


def main() -> None:
    setup_logging()
    settings = get_settings()
    components = create_components(settings)
    canonical = canonical_url_map(load_jsonl(settings.data_dir / "clean" / "pages.jsonl"))

    answerable = []
    for item in load_jsonl(EVAL_DIR / "golden_set.jsonl"):
        result = score_question(components, settings, item["question"])
        expected = {canonical[url] for url in item["expected_urls"]}
        result["correct_in_context"] = any(
            canonical.get(url, url) in expected for url in result["urls"]
        )
        answerable.append({"id": item["id"], **result})
        logger.info(f"{item['id']}: score={result['score']}")

    unanswerable = []
    for item in load_jsonl(EVAL_DIR / "negative_set.jsonl"):
        result = score_question(components, settings, item["question"])
        unanswerable.append({"id": item["id"], **result})
        logger.info(f"{item['id']}: intent={result['intent']} score={result['score']}")

    print("\nMejor puntaje del reranker por pregunta")
    print("Respondibles (golden set):")
    for row in sorted(answerable, key=lambda r: r["score"] or -99):
        mark = "ok" if row["correct_in_context"] else "SIN la página correcta"
        print(f"  {row['id']}  {row['score'] if row['score'] is not None else '-':>6}  {mark}")
    print("Sin respuesta en el corpus:")
    for row in sorted(unanswerable, key=lambda r: r["score"] or -99):
        score = f"{row['score']:.2f}" if row["score"] is not None else f"({row['intent']})"
        print(f"  {row['id']}  {score:>6}")

    scored_ok = [
        r["score"] for r in answerable if r["score"] is not None and r["correct_in_context"]
    ]
    scored_neg = [r["score"] for r in unanswerable if r["score"] is not None]
    print("\nUmbral   respondibles aceptadas   sin respuesta rechazadas")
    table = []
    for threshold in THRESHOLDS:
        accepted = sum(s >= threshold for s in scored_ok) / len(scored_ok)
        rejected = sum(s < threshold for s in scored_neg) / len(scored_neg) if scored_neg else 1.0
        table.append({"threshold": threshold, "accepted": accepted, "rejected": rejected})
        print(f"{threshold:>6}   {accepted:>21.0%}   {rejected:>24.0%}")

    report = {"answerable": answerable, "unanswerable": unanswerable, "table": table}
    output = EVAL_DIR / "results" / "threshold.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Report saved to {output}")


if __name__ == "__main__":
    main()

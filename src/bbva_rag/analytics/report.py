"""Informe analítico en la terminal.
Ejecutar con: python -m bbva_rag.analytics.report [--days N] [--topics]"""

import argparse
from datetime import UTC, datetime, timedelta

from bbva_rag.analytics.metrics import build_exchanges, summarize
from bbva_rag.analytics.topics import cluster_questions
from bbva_rag.config import get_settings, setup_logging
from bbva_rag.embeddings.factory import create_embedder
from bbva_rag.memory.database import create_session_factory
from bbva_rag.memory.repository import ConversationRepository


def pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.0%}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Analytics over the conversation history.")
    parser.add_argument("--days", type=int, help="only the last N days")
    parser.add_argument("--topics", action="store_true", help="cluster questions into topics")
    args = parser.parse_args()

    setup_logging()
    settings = get_settings()
    repository = ConversationRepository(create_session_factory(settings.database_url))
    since = datetime.now(UTC) - timedelta(days=args.days) if args.days else None
    exchanges = build_exchanges(repository.all_messages(since))
    if not exchanges:
        print("Todavía no hay conversaciones.")
        return
    s = summarize(exchanges, settings.analytics_minutes_saved_per_answer)

    print("\n=== Uso ===")
    print(
        f"Preguntas: {s['questions']}  |  conversaciones: {s['conversations']}  |  "
        f"preguntas por conversación: {s['questions_per_conversation']:.1f}"
    )
    print(f"Intenciones: {s['intents']}")

    print("\n=== Calidad ===")
    print(f"Resultados: {s['outcomes']}")
    print(f"Tasa de respuesta (preguntas del banco): {pct(s['answer_rate'])}")
    print(f"Tasa de reformulación: {pct(s['rewrite_rate'])}")
    print(
        f"Satisfacción: {pct(s['feedback']['positive_rate'])} "
        f"de {s['feedback']['rated']} calificadas"
    )

    print("\n=== Latencia ===")
    print(f"p50: {s['latency_p50_seconds']:.1f} s  |  p95: {s['latency_p95_seconds']:.1f} s")
    print(
        "Promedio por nodo: " + "  ".join(f"{k}={v:.1f}s" for k, v in s["avg_node_seconds"].items())
    )

    print("\n=== Contenido más consultado ===")
    for source in s["top_sources"][:5]:
        print(f"  {source['citations']:>3}  {source['title']}")
    print(f"Secciones: {s['top_sections']}")

    print("\n=== Preguntas sin respuesta (vacíos de contenido) ===")
    for item in s["unanswered_questions"]:
        print(f"  - {item['question']}")

    impact = s["impact"]
    print("\n=== Impacto ===")
    print(
        f"{impact['answered_questions']} preguntas respondidas × "
        f"{impact['minutes_saved_per_answer']:.0f} min = "
        f"{impact['estimated_hours_saved']:.1f} horas de búsqueda manual ahorradas (estimado)"
    )

    if args.topics:
        print("\n=== Temas más consultados ===")
        questions = [e["question"] for e in exchanges if e["intent"] == "bank_query"]
        for topic in cluster_questions(
            questions, create_embedder(settings), settings.analytics_max_topics
        ):
            print(f"  [{topic['size']} preguntas] {', '.join(topic['keywords'])}")
            for example in topic["examples"]:
                print(f"      · {example}")


if __name__ == "__main__":
    main()

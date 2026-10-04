"""Métricas de uso, calidad e impacto calculadas a partir del historial de conversaciones"""

from collections import Counter, defaultdict
from statistics import mean

from bbva_rag.cleaning.run import section_from_url


def build_exchanges(messages: list[dict]) -> list[dict]:
    """Asocia cada respuesta del asistente con la
    pregunta del usuario que la precedió"""
    exchanges, last_question = [], {}
    for message in messages:  # ordered by id
        if message["role"] == "user":
            last_question[message["conversation_id"]] = message["content"]
        elif message["role"] == "assistant":
            question = last_question.get(message["conversation_id"], "")
            exchanges.append({**message, "question": question})
    return exchanges


def percentile(values: list[float], p: float) -> float | None:
    """Percentil de rango más cercano (funciona con pocos valores)"""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round(p / 100 * (len(ordered) - 1))]


def rate(part: int, total: int) -> float | None:
    return part / total if total else None


def summarize(exchanges: list[dict], minutes_saved_per_answer: float) -> dict:
    bank = [e for e in exchanges if e["intent"] == "bank_query"]
    outcomes = Counter(e["outcome"] or "unknown" for e in exchanges)
    conversations = {e["conversation_id"] for e in exchanges}
    latencies = [e["latency_seconds"] for e in exchanges if e["latency_seconds"] is not None]
    ratings = [e["feedback"] for e in exchanges if e["feedback"] is not None]
    answered = outcomes.get("answered", 0)

    node_seconds = defaultdict(list)
    for e in exchanges:
        per_node = defaultdict(float)
        for key, seconds in e["timings"].items():
            per_node[key.split("_")[0]] += seconds  # retrieve_1 + retrieve_2 -> retrieve
        for node, seconds in per_node.items():
            node_seconds[node].append(seconds)

    citations = Counter(
        (source["title"], source["url"]) for e in exchanges for source in e["sources"]
    )
    sections = Counter()
    for (_, url), count in citations.items():
        sections[section_from_url(url)] += count

    return {
        "questions": len(exchanges),
        "conversations": len(conversations),
        "questions_per_conversation": rate(len(exchanges), len(conversations)),
        "questions_per_day": dict(
            sorted(Counter(e["created_at"].date().isoformat() for e in exchanges).items())
        ),
        "intents": dict(Counter(e["intent"] or "unknown" for e in exchanges)),
        "outcomes": dict(outcomes),
        "answer_rate": rate(answered, len(bank)),
        "rewrite_rate": rate(sum((e["attempts"] or 0) > 1 for e in bank), len(bank)),
        "latency_p50_seconds": percentile(latencies, 50),
        "latency_p95_seconds": percentile(latencies, 95),
        "avg_node_seconds": {node: mean(values) for node, values in node_seconds.items()},
        "feedback": {
            "rated": len(ratings),
            "positive_rate": rate(sum(r == 1 for r in ratings), len(ratings)),
        },
        "top_sources": [
            {"title": title, "url": url, "citations": count}
            for (title, url), count in citations.most_common(10)
        ],
        "top_sections": dict(sections.most_common()),
        "unanswered_questions": [
            {
                "question": e["question"],
                "standalone_question": e["standalone_question"],
                "date": e["created_at"].isoformat(),
            }
            for e in exchanges
            if e["outcome"] == "no_answer"
        ],
        "impact": {
            "answered_questions": answered,
            "minutes_saved_per_answer": minutes_saved_per_answer,
            "estimated_hours_saved": answered * minutes_saved_per_answer / 60,
        },
    }

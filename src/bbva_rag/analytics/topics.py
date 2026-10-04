"""Agrupa las preguntas de los usuarios por temas: incrustaciones + K-Means, eligiendo
k según la puntuación de silueta"""

import re
from collections import Counter

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from bbva_rag.embeddings.base import Embedder

STOPWORDS = {
    "como",
    "cómo",
    "cual",
    "cuál",
    "cuales",
    "cuáles",
    "cuanto",
    "cuánto",
    "cuanta",
    "cuánta",
    "para",
    "puedo",
    "tengo",
    "tiene",
    "tienen",
    "este",
    "esta",
    "esto",
    "sobre",
    "donde",
    "dónde",
    "cuando",
    "cuándo",
    "hacer",
    "quiero",
    "bancolombia",
    "banco",
    "porque",
    "desde",
}


def top_keywords(questions: list[str], limit: int = 4) -> list[str]:
    words = Counter(
        word
        for question in questions
        for word in re.findall(r"[a-záéíóúñü]+", question.lower())
        if len(word) >= 3 and word not in STOPWORDS
    )
    return [word for word, _ in words.most_common(limit)]


def cluster_questions(questions: list[str], embedder: Embedder, max_topics: int = 6) -> list[dict]:
    unique = list(dict.fromkeys(q.strip() for q in questions if q.strip()))
    if len(unique) < 4:
        return []
    vectors = np.array(embedder.embed_documents(unique))
    distinct_points = len(np.unique(vectors, axis=0))
    max_k = min(max_topics, len(unique) - 1, distinct_points)
    if max_k < 2:
        return []

    best = None
    for k in range(2, max_k + 1):
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(vectors)
        score = silhouette_score(vectors, labels, metric="cosine")
        if best is None or score > best[0]:
            best = (score, k, labels)
    _, k, labels = best

    topics = []
    for cluster in range(k):
        members = [q for q, label in zip(unique, labels, strict=True) if label == cluster]
        topics.append(
            {"size": len(members), "keywords": top_keywords(members), "examples": members[:3]}
        )
    return sorted(topics, key=lambda topic: topic["size"], reverse=True)

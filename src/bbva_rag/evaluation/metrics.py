"""Métricas de recuperación calculadas a partir del rango
de la primera página correcta para cada pregunta"""


def first_hit_rank(retrieved_urls: list[str], expected_urls: set[str]) -> int | None:
    """Posición basada en 1 de la primera página correcta, o Ninguna si no se recuperó ninguna"""
    for rank, url in enumerate(retrieved_urls, start=1):
        if url in expected_urls:
            return rank
    return None


def hit_rate(ranks: list[int | None], k: int) -> float:
    """Porcentaje de preguntas cuya página correcta aparece en la parte superior"""
    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks)


def mean_reciprocal_rank(ranks: list[int | None]) -> float:
    """Promedio de 1/rango (0 cuando no se recuperó la página correcta)"""
    return sum(1 / rank for rank in ranks if rank is not None) / len(ranks)

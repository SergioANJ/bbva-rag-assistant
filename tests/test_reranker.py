from bbva_rag.retrieval.base import RetrievedChunk
from bbva_rag.retrieval.reranker import CrossEncoderReranker


def make_chunk(name: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(f"id-{name}", f"https://x.com/{name}", name, "personas", name, score)


class FakeCrossEncoder:
    """Clasifica cada texto según su longitud: texto más largo = más relevante"""

    def rerank(self, query, documents):
        return [float(len(doc)) for doc in documents]


def test_reranker_reorders_by_new_score_and_keeps_top_n():
    chunks = [make_chunk("a", 0.9), make_chunk("ccc", 0.5), make_chunk("bb", 0.1)]
    reranked = CrossEncoderReranker("fake", encoder=FakeCrossEncoder()).rerank("q", chunks, top_n=2)
    assert [c.title for c in reranked] == ["ccc", "bb"]


def test_reranker_replaces_the_score():
    chunks = [make_chunk("ccc", 0.5)]
    [reranked] = CrossEncoderReranker("fake", encoder=FakeCrossEncoder()).rerank("q", chunks, 1)
    assert reranked.score == 3.0


def test_reranker_handles_no_candidates():
    assert CrossEncoderReranker("fake", encoder=FakeCrossEncoder()).rerank("q", [], 5) == []

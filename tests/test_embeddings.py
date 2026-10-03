from types import SimpleNamespace

import pytest

from bbva_rag.config import Settings
from bbva_rag.embeddings.factory import create_embedder
from bbva_rag.embeddings.openai_embedder import OpenAIEmbedder


class FakeEmbeddingsAPI:
    """Imita client.embeddings: devuelve [i] como el vector del texto i,
    en orden inverso."""

    def __init__(self):
        self.calls = 0

    def create(self, model, input, dimensions):
        self.calls += 1
        data = [SimpleNamespace(index=i, embedding=[float(len(t))]) for i, t in enumerate(input)]
        return SimpleNamespace(data=list(reversed(data)))


def make_embedder(batch_size: int) -> tuple[OpenAIEmbedder, FakeEmbeddingsAPI]:
    api = FakeEmbeddingsAPI()
    client = SimpleNamespace(embeddings=api)
    return OpenAIEmbedder("key", "model", 1, batch_size=batch_size, client=client), api


def test_texts_are_sent_in_batches():
    embedder, api = make_embedder(batch_size=100)
    vectors = embedder.embed_documents(["texto"] * 250)
    assert api.calls == 3
    assert len(vectors) == 250


def test_vectors_keep_the_order_of_the_texts():
    embedder, _ = make_embedder(batch_size=10)
    vectors = embedder.embed_documents(["a", "bb", "ccc"])
    assert vectors == [[1.0], [2.0], [3.0]]


def test_factory_requires_api_key():
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        create_embedder(Settings(_env_file=None, openai_api_key=None))

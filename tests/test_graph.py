from bbva_rag.config import Settings
from bbva_rag.graph.builder import build_graph
from bbva_rag.graph.nodes import NO_ANSWER_MESSAGE, RAGNodes
from bbva_rag.retrieval.base import RetrievedChunk

SETTINGS = Settings(_env_file=None, relevance_threshold=0.5, max_query_rewrites=1)


def chunk(score: float) -> RetrievedChunk:
    return RetrievedChunk("id", "https://x.com/cdt", "CDT", "personas", "texto", score)


class StubNodes(RAGNodes):
    """Real routing logic, fake external calls. Records the path followed."""

    def __init__(self, intent: str, scores: list[float]):
        super().__init__(llm=None, retriever=None, reranker=None, settings=SETTINGS)
        self.intent, self.scores, self.path = intent, list(scores), []

    def analyze_query(self, state):
        self.path.append("analyze_query")
        return {"intent": self.intent, "standalone_question": state["question"],
                "answer": "¡Hola!" if self.intent != "bank_query" else "", "attempts": 0}

    def retrieve(self, state):
        self.path.append("retrieve")
        return {"candidates": [], "attempts": state["attempts"] + 1}

    def rerank(self, state):
        self.path.append("rerank")
        return {"context": [chunk(self.scores.pop(0))]}

    def rewrite_query(self, state):
        self.path.append("rewrite_query")
        return {"standalone_question": "pregunta reformulada"}

    def generate(self, state):
        self.path.append("generate")
        return {"answer": "respuesta [1]", "sources": [{"title": "CDT", "url": "https://x.com/cdt"}]}


def run(nodes: StubNodes) -> dict:
    return build_graph(nodes).invoke({"question": "¿Qué es un CDT?", "history": []})


def test_greeting_skips_retrieval():
    nodes = StubNodes("greeting", scores=[])
    result = run(nodes)
    assert nodes.path == ["analyze_query"]
    assert result["answer"] == "¡Hola!"


def test_relevant_context_goes_straight_to_generate():
    nodes = StubNodes("bank_query", scores=[0.9])
    result = run(nodes)
    assert nodes.path == ["analyze_query", "retrieve", "rerank", "generate"]
    assert result["sources"][0]["url"] == "https://x.com/cdt"


def test_low_score_triggers_one_rewrite_then_generates():
    nodes = StubNodes("bank_query", scores=[0.1, 0.9])
    run(nodes)
    assert nodes.path == [
        "analyze_query", "retrieve", "rerank", "rewrite_query", "retrieve", "rerank", "generate"
    ]


def test_no_relevant_context_after_rewrite_gives_honest_answer():
    nodes = StubNodes("bank_query", scores=[0.1, 0.2])
    result = run(nodes)
    assert nodes.path[-2:] == ["rerank", "no_answer"] or nodes.path[-1] == "rerank"
    assert result["answer"] == NO_ANSWER_MESSAGE
    assert result["attempts"] == 2
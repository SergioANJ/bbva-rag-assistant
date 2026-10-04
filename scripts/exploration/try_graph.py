"""Exploración: ejecute el gráfico RAG para una pregunta 
   y muestre la ruta y los tiempos"""
import sys

from bbva_rag.config import get_settings
from bbva_rag.graph.builder import create_rag_graph


def main(question: str) -> None:
    graph = create_rag_graph(get_settings())
    result = graph.invoke({"question": question, "history": []})

    print(f"Intención: {result['intent']}")
    print(f"Pregunta usada para buscar: {result.get('standalone_question')}")
    print(f"Búsquedas realizadas: {result.get('attempts', 0)}")
    if result.get("context"):
        print(f"Mejor puntaje del reranker: {result['context'][0].score:.2f}")
    print(f"\nRespuesta:\n{result['answer']}\n")
    for source in result.get("sources", []):
        print(f"  - {source['title']}: {source['url']}")
    timings = result.get("timings", {})
    print("\nTiempos: " + "  ".join(f"{k}={v:.1f}s" for k, v in timings.items()))
    print(f"Total: {sum(timings.values()):.1f}s")


if __name__ == "__main__":
    main(sys.argv[1].strip())
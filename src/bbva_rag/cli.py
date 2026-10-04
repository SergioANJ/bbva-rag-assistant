"""Conversación en la terminal con el asistente RAG (historial en memoria; la persistencia se
   piensa implementa en la fase 5)"""

from loguru import logger

from bbva_rag.config import get_settings, setup_logging
from bbva_rag.graph.builder import create_rag_graph

EXIT_COMMANDS = {"salir", "exit", "quit"}


def recent_history(history: list[dict], max_messages: int) -> list[dict]:
    """Last N messages. Careful: history[-0:] would return the whole list."""
    return history[-max_messages:] if max_messages > 0 else []


def main() -> None:
    setup_logging()
    settings = get_settings()
    print("Cargando el asistente...")
    graph = create_rag_graph(settings)
    history: list[dict] = []
    print("Asistente de Bancolombia. Escribe tu pregunta, '/nueva' para reiniciar o 'salir'.\n")

    while True:
        try:
            question = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in EXIT_COMMANDS:
            break
        if question == "/nueva":
            history.clear()
            print("(conversación reiniciada)\n")
            continue

        try:
            result = graph.invoke(
                {"question": question, "history": recent_history(history, settings.history_max_messages)}
            )
        except Exception:
            logger.exception("Error while answering")
            print("\nAsistente: Ocurrió un error al procesar tu pregunta. Intenta de nuevo.\n")
            continue

        print(f"\nAsistente: {result['answer']}")
        for source in result.get("sources", []):
            print(f"  - {source['title']}: {source['url']}")
        print(f"  ({sum(result.get('timings', {}).values()):.1f} s)\n")

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": result["answer"]})

    print("¡Hasta luego!")


if __name__ == "__main__":
    main()
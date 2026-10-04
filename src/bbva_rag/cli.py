"""Conversación en terminal con el asistente RAG e
historial persistente en PostgreSQL"""

import argparse
import uuid

from bbva_rag.config import get_settings, setup_logging
from bbva_rag.graph.builder import create_rag_graph
from bbva_rag.memory.database import create_session_factory
from bbva_rag.memory.repository import ConversationRepository
from bbva_rag.services.chat import ChatService

EXIT_COMMANDS = {"salir", "exit", "quit"}
HELP = (
    "Comandos: /nueva (otra conversación), /util o /noutil (calificar la última respuesta), salir"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the Bancolombia RAG assistant.")
    parser.add_argument("--session", help="conversation id to resume")
    args = parser.parse_args()

    setup_logging()
    settings = get_settings()
    print("Cargando el asistente...")
    repository = ConversationRepository(create_session_factory(settings.database_url))
    chat = ChatService(create_rag_graph(settings), repository, settings.history_max_messages)

    conversation_id = args.session or str(uuid.uuid4())
    last_message_id = None
    print(f"Conversación: {conversation_id}\n{HELP}\n")

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
            conversation_id, last_message_id = str(uuid.uuid4()), None
            print(f"(nueva conversación: {conversation_id})\n")
            continue
        if question in ("/util", "/noutil"):
            if last_message_id is None:
                print("(todavía no hay una respuesta para calificar)\n")
            else:
                repository.set_feedback(last_message_id, 1 if question == "/util" else -1)
                print("(¡gracias por tu calificación!)\n")
            continue

        reply = chat.ask(conversation_id, question)
        last_message_id = reply.message_id
        print(f"\nAsistente: {reply.answer}")
        for source in reply.sources:
            print(f"  - {source['title']}: {source['url']}")
        print(f"  ({reply.latency_seconds:.1f} s)\n")

    print(f"¡Hasta luego! Para retomar: uv run python -m bbva_rag.cli --session {conversation_id}")


if __name__ == "__main__":
    main()

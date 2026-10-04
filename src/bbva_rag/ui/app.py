"""Interfaz de usuario de chat. Ejecutar con: streamlit
run src/bbva_rag/ui/app.py (la API debe estar en ejecución)"""

import uuid

import httpx
import streamlit as st

from bbva_rag.config import get_settings

API = get_settings().api_base_url
TIMEOUT = (
    120  # Las respuestas sin contexto pueden tardar unos 15 segundos; se deja un margen amplio
)

st.set_page_config(page_title="Asistente Bancolombia", page_icon="🏦")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

with st.sidebar:
    st.header("Asistente Bancolombia")
    st.caption("Responde con la información publicada en bancolombia.com, citando sus fuentes.")
    if st.button("Nueva conversación", use_container_width=True):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.rerun()
    resume = st.text_input("Retomar conversación (ID)")
    if st.button("Retomar", use_container_width=True) and resume.strip():
        st.session_state.conversation_id = resume.strip()
        st.rerun()
    st.caption(f"ID actual: `{st.session_state.conversation_id}`")


def send_feedback(message_id: int, value: int) -> None:
    httpx.post(f"{API}/messages/{message_id}/feedback", json={"value": value}, timeout=10)


try:
    response = httpx.get(
        f"{API}/conversations/{st.session_state.conversation_id}/messages", timeout=10
    )
    response.raise_for_status()
    messages = response.json()
except httpx.HTTPError as error:
    st.error(f"No se pudo cargar la conversación desde la API ({API}): {error}")
    st.stop()

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if message["sources"]:
                with st.expander("Fuentes"):
                    for source in message["sources"]:
                        st.markdown(f"- [{source['title']}]({source['url']})")
            if message["feedback"] is None:
                up, down, _ = st.columns([1, 1, 10])
                if up.button("👍", key=f"up-{message['id']}"):
                    send_feedback(message["id"], 1)
                    st.rerun()
                if down.button("👎", key=f"down-{message['id']}"):
                    send_feedback(message["id"], -1)
                    st.rerun()
            else:
                st.caption("Calificada: " + ("👍" if message["feedback"] == 1 else "👎"))

if question := st.chat_input("Escribe tu pregunta sobre Bancolombia..."):
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"), st.spinner("Buscando en el sitio de Bancolombia..."):
        try:
            response = httpx.post(
                f"{API}/chat",
                json={"question": question, "conversation_id": st.session_state.conversation_id},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            st.error("No se pudo obtener una respuesta. Intenta de nuevo.")
            st.stop()
    st.rerun()

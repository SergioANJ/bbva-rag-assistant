""" "Panel de análisis (lee GET /analytics desde la API)."""

import httpx
import pandas as pd
import streamlit as st

from bbva_rag.config import get_settings

API = get_settings().api_base_url

st.set_page_config(page_title="Analítica", page_icon="📊", layout="wide")
st.title("📊 Analítica del asistente")

days = st.sidebar.selectbox(
    "Periodo", [None, 7, 30, 90], format_func=lambda d: "Todo" if d is None else f"Últimos {d} días"
)
with_topics = st.sidebar.checkbox("Calcular temas (usa embeddings)", value=False)

params = {"topics": with_topics} | ({"days": days} if days else {})
try:
    response = httpx.get(f"{API}/analytics", params=params, timeout=120)
    response.raise_for_status()
    data = response.json()
except httpx.HTTPError as error:
    st.error(f"No se pudo cargar la analítica desde la API: {error}")
    st.stop()

if data["questions"] == 0:
    st.info("Todavía no hay conversaciones en este periodo.")
    st.stop()


def pct(value):
    return "-" if value is None else f"{value:.0%}"


c1, c2, c3, c4 = st.columns(4)
c1.metric("Preguntas", data["questions"])
c2.metric("Conversaciones", data["conversations"])
c3.metric("Tasa de respuesta", pct(data["answer_rate"]))
c4.metric(
    "Satisfacción",
    pct(data["feedback"]["positive_rate"]),
    f"{data['feedback']['rated']} calificadas",
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Horas ahorradas (estimado)", f"{data['impact']['estimated_hours_saved']:.1f}")
c2.metric("Latencia p50", f"{data['latency_p50_seconds']:.1f} s")
c3.metric("Latencia p95", f"{data['latency_p95_seconds']:.1f} s")
c4.metric("Tasa de reformulación", pct(data["rewrite_rate"]))

left, right = st.columns(2)
with left:
    st.subheader("Preguntas por día")
    st.bar_chart(pd.Series(data["questions_per_day"], name="preguntas"))
    st.subheader("Resultados")
    st.bar_chart(pd.Series(data["outcomes"], name="preguntas"))
with right:
    st.subheader("Tiempo promedio por etapa (s)")
    st.bar_chart(pd.Series(data["avg_node_seconds"], name="segundos"))
    st.subheader("Secciones más citadas")
    st.bar_chart(pd.Series(data["top_sections"], name="citas"))

st.subheader("Páginas más citadas")
st.dataframe(pd.DataFrame(data["top_sources"]), use_container_width=True, hide_index=True)

st.subheader("Preguntas sin respuesta (vacíos de contenido)")
if data["unanswered_questions"]:
    st.dataframe(
        pd.DataFrame(data["unanswered_questions"]), use_container_width=True, hide_index=True
    )
else:
    st.caption("Ninguna en este periodo.")

if with_topics and data.get("topics"):
    st.subheader("Temas más consultados")
    for topic in data["topics"]:
        with st.expander(f"{', '.join(topic['keywords'])} ({topic['size']} preguntas)"):
            for example in topic["examples"]:
                st.markdown(f"- {example}")

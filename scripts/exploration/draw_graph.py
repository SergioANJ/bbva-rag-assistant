""" "Imprime el gráfico RAG como un diagrama de Mermaid
(https://mermaid.live)"""

from bbva_rag.config import get_settings
from bbva_rag.graph.builder import create_rag_graph

print(create_rag_graph(get_settings()).get_graph().draw_mermaid())

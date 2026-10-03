""" Interfaz, que define como debe comportarse 
    cualquier clase que genere embeddings en el proyecto"""


from typing import Protocol

class Embedder(Protocol):
    dimensions: int

    def embed_documents_(self, texts: list[str]) -> list[list[float]]:
        """"Vectorizar varios textos (utilizados en el momento
        de la indexación)."""
        

    def embed_query(self, text: str) -> list[float]:
        """"Vectoriza una pregunta de usuario (
        utilizada en el momento de la consulta)."""
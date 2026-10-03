"""Exploración: mouestra cómo las incrustaciones capturan el
significado (similitud del coseno entre oraciones)."""

from bbva_rag.config import get_settings
from bbva_rag.embeddings.factory import create_embedder

SENTENCES = [
    "¿Cuánto me cobran por tener la tarjeta de crédito?",
    "Cuota de manejo de la tarjeta de crédito",
    "Cómo abrir un CDT por la app",
    "Invertir a término fijo con certificado de depósito",
    "Horario de atención de las oficinas",
]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)


def main() -> None:
    embedder = create_embedder(get_settings())
    vectors = embedder.embed_documents(SENTENCES)
    print(f"Dimensiones de cada vector: {len(vectors[0])}\n")
    for i, sentence in enumerate(SENTENCES):
        scores = [f"{cosine(vectors[i], v):.2f}" for v in vectors]
        print(f"{' '.join(scores)}   {sentence}")


if __name__ == "__main__":
    main()

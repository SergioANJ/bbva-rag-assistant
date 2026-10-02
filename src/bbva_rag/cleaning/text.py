"""PASO A, limpiesza por página"""

import re

import trafilatura
from parsel import Selector

# Nombres de componentes internos del portal IBM WebSphere que se filtran en el texto
PORTAL_ARTIFACT_LINES = {
    "{}",
    "web content viewer",
    "display portlet menu",
    "component action menu",
    "deferred modules",
}
TEMPLATE_PLACEHOLDER = re.compile(r"\$\{[^}]*\}")  # ${title}, ${loading}
ICON_TEXT = re.compile(r"\*arrow-(?:left|right)\*")
COMPONENT_NAME = re.compile(r"^#*\s*[A-Z][a-z]+(?:[A-Z][A-Za-z]*)+$")  # BannerCentroAyuda
MULTIPLE_BLANK_LINES = re.compile(r"\n{3,}")


def extract_main_text(html: str) -> str:
    """Contenido principal de la página en formato Markdown 
    (cadena vacía si no se encuentra nada)."""
    return trafilatura.extract(html, output_format="markdown", include_tables=True) or ""


def extract_title(html: str) -> str:
    """Preferir la etiqueta <h1> de la página; si falta el h1
    o es un marcador de posición, se utilizará <title>."""
    selector = Selector(text=html)
    h1 = " ".join(t.strip() for t in selector.css("h1 ::text").getall() if t.strip())
    h1 = TEMPLATE_PLACEHOLDER.sub("", h1).strip()
    return h1 or selector.css("title::text").get(default="").strip()


def remove_portal_artifacts(text: str) -> str:
    """Arrastre los marcadores de posición de la plantilla, las etiquetas de los iconos
    y los nombres de los componentes del portal."""
    text = TEMPLATE_PLACEHOLDER.sub("", text)
    text = ICON_TEXT.sub("", text)
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        bare = stripped.lstrip("#").strip()
        if bare.lower() in PORTAL_ARTIFACT_LINES or COMPONENT_NAME.match(stripped):
            continue
        kept.append(line)
    return "\n".join(kept)


def normalize_whitespace(text: str) -> str:
    """SEliminar cada línea, reemplazar los espacios de no separación
    y eliminar las secuencias de líneas en blanco."""
    text = text.replace("\xa0", " ")
    text = "\n".join(line.strip() for line in text.splitlines())
    return MULTIPLE_BLANK_LINES.sub("\n\n", text).strip()


def clean_page(html: str) -> str:
    """Limpieza completa página por página: extracción, eliminación de artefactos, normalización."""
    return normalize_whitespace(remove_portal_artifacts(extract_main_text(html)))

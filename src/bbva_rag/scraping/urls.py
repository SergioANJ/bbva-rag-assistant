"""Funciones para limpiar y filtrar URLS durante el proceso de scraping"""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PREFIXES = ("utm_",)


def canonicalize_url(url: str) -> str:
    """Elimina parámetros de seguimiento publicitario (como utm_source, utm_campaign)
    y anclas de navegación."""
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith(TRACKING_PREFIXES)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def is_excluded(url: str, patterns: list[str]) -> bool:
    """Revisa si la URL contiene alguna de las palabras prohibidas definidas en configuración
    como simulador, llamanis..."""
    lowered = url.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def is_soft_404(requested_url: str, final_url: str, soft404_paths: list[str]) -> bool:
    """Comprueba si al solicitar una URL que ya no existe, el sitio web te redirigió
    silenciosamente a una portada genérica eje:/personas"""
    if requested_url == final_url:
        return False
    final_path = urlsplit(final_url).path.rstrip("/")
    return final_path in {path.rstrip("/") for path in soft404_paths}

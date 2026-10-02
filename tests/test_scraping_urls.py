"""Cada uno de estos test, corresponde a un caso real encontrado en la exploración de la info.
redicción de renta-fija, simularodores.."""

from bbva_rag.scraping.urls import canonicalize_url, is_excluded, is_soft_404

HOME = "https://www.bancolombia.com/personas"


def test_canonicalize_removes_utm_params():
    url = (
        "https://valores.bancolombia.com/productos-servicios/renta-fija"
        "?utm_source=redirect&utm_medium=organic&utm_campaign=inversiones"
    )
    assert canonicalize_url(url) == "https://valores.bancolombia.com/productos-servicios/renta-fija"


def test_canonicalize_keeps_other_params_and_drops_fragment():
    assert canonicalize_url("https://x.com/a?id=5&utm_source=y#top") == "https://x.com/a?id=5"


def test_is_excluded_is_case_insensitive():
    assert is_excluded("https://x.com/inversiones/Simulador-CDT", ["simulador"])
    assert not is_excluded("https://x.com/inversiones/renta-fija", ["simulador"])


def test_redirect_to_landing_is_soft_404():
    assert is_soft_404(f"{HOME}/articulo-borrado", HOME, ["/personas"])


def test_redirect_to_real_page_is_not_soft_404():
    assert not is_soft_404(f"{HOME}/app-inversiones", f"{HOME}/canales/app", ["/personas"])


def test_direct_visit_to_landing_is_not_soft_404():
    assert not is_soft_404(HOME, HOME, ["/personas"])

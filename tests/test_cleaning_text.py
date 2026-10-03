from bbva_rag.cleaning.text import extract_title, normalize_whitespace, remove_portal_artifacts


def test_removes_portal_component_lines():
    text = "## BannerCentroAyuda\nDisplay portlet menu\n## Web Content Viewer\n# Centro de Ayuda"
    assert remove_portal_artifacts(text).strip() == "# Centro de Ayuda"


def test_removes_placeholders_and_icons():
    text = "*arrow-right*\n${title}${badge}\nCDT desmaterializado"
    assert remove_portal_artifacts(text).strip() == "CDT desmaterializado"


def test_keeps_real_headings():
    text = "## Beneficios\n## Requisitos del crédito"
    assert remove_portal_artifacts(text) == text


def test_normalize_whitespace():
    assert normalize_whitespace("  Hola\xa0mundo  \n\n\n\n  Chao ") == "Hola mundo\n\nChao"
    assert normalize_whitespace("Plan Cero      (sin IVA)") == "Plan Cero (sin IVA)"


def test_title_prefers_h1_and_skips_placeholders():
    html = "<html><head><title>Genérico</title></head><body><h1>${title}</h1></body></html>"
    assert extract_title(html) == "Genérico"
    html = (
        "<html><head><title>Genérico</title></head><body><h1>¿Qué es el vishing?</h1></body></html>"
    )
    assert extract_title(html) == "¿Qué es el vishing?"

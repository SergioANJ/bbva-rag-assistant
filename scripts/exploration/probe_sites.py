"""Temporary script: check which bank sites allow automated access."""

import httpx

UA = "Mozilla/5.0 (compatible; bbva-rag-assistant/0.1; +https://github.com/SergioANJ/bbva-rag-assistant)"
HEADERS = {"User-Agent": UA, "Accept-Language": "es-CO,es;q=0.9"}

SITES = [
    "https://www.bbva.com.co",
    "https://www.bancolombia.com",
    "https://www.davivienda.com",
    "https://www.bancodebogota.com",
    "https://www.bancopopular.com.co",
    "https://www.bancodeoccidente.com.co",
    "https://www.avvillas.com.co",
    "https://www.bancocajasocial.com",
]

for base in SITES:
    try:
        page = httpx.get(base, headers=HEADERS, follow_redirects=True, timeout=15)
        robots = httpx.get(f"{base}/robots.txt", headers=HEADERS, timeout=15)
        print(
            f"{base:40} page={page.status_code}size={len(page.text):>7} robots={robots.status_code}"
        )
    except httpx.HTTPError as exc:
        print(f"{base:40} ERROR {type(exc).__name__}")

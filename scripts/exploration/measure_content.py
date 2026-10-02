"""Exploration: measure extracted text per page type (one-off analysis)."""

import time

import httpx
import trafilatura

UA = (
    "Mozilla/5.0 (compatible; bbva-rag-assistant/0.1; "
    "+https://github.com/SergioANJ/bbva-rag-assistant)"
)
P = "https://www.bancolombia.com/personas/productos-servicios/inversiones"

SAMPLE = {
    "producto": [
        f"{P}/renta-fija",
        f"{P}/fondos-inversion-colectiva",
        f"{P}/inversiones-digitales",
    ],
    "simulador": [
        f"{P}/cdts/fisicos/simulador-cdt",
        f"{P}/fondos-inversion-colectiva/fiducuenta/simulador-ahorro-inversion",
    ],
    "contacto": [
        f"{P}/fondos-inversion-colectiva/llamanos",
        f"{P}/fondos-inversion-colectiva/chatea-con-nosotros",
    ],
    "ayuda": [
        "https://www.bancolombia.com/centro-de-ayuda",
        "https://www.bancolombia.com/centro-de-ayuda/canales/app-inversiones",
    ],
    "historia": [
        "https://www.bancolombia.com/acerca-de/informacion-corporativa/historias-que-transforman/origenes/agroindustria/agrollanos"
    ],
    "educacion": [
        "https://www.bancolombia.com/personas/aprender-es-facil/como-manejar-dinero/invertir/realizar-inversiones-periodicas",
        "https://www.bancolombia.com/centro-de-ayuda",
        "https://www.bancolombia.com/centro-de-ayuda/canales/corresponsal-bancari",
    ],
}


def main() -> None:
    with httpx.Client(headers={"User-Agent": UA}, timeout=20, follow_redirects=True) as client:
        for page_type, urls in SAMPLE.items():
            for url in urls:
                time.sleep(1.5)
                response = client.get(url)
                final_url = str(response.url)
                redirect = (
                    ""
                    if final_url.rstrip("/") == url.rstrip("/")
                    else f"  -> REDIRIGE A {final_url}"
                )

                precise = (
                    trafilatura.extract(
                        response.text, output_format="markdown", include_tables=True
                    )
                    or ""
                )
                recall = (
                    trafilatura.extract(
                        response.text,
                        output_format="markdown",
                        include_tables=True,
                        favor_recall=True,
                    )
                    or ""
                )

                name = url.rstrip("/").rsplit("/", 1)[-1]
                print(
                    f"[{page_type:9}] {response.status_code}  html={len(response.text):>7}  "
                    f"precision={len(precise):>5}  recall={len(recall):>5}  {name}{redirect}"
                )
                print(f"             {recall[:200]!r}\n")


if __name__ == "__main__":
    main()

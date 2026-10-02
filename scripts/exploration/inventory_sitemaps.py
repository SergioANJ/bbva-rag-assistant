import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import httpx
from parsel import Selector
from protego import Protego

BASE = "https://www.bancolombia.com"

UA = "Mozilla/5.0 (compatible; bbva-rag-assistant/0.1; +https://github.com/SergioANJ/bbva-rag-assistant)"

NOISE_PATTERNS = [
    "simulador",
    "llamanos",
    "chatea",
    "-viejo",
    "-old",
    "formulario",
    "prueba",
    "test",
]
OUTPUT = Path(__file__).parent / "urls.txt"


def get_locs(client: httpx.Client, url: str) -> list[str]:
    """Download a sitemap and return every <loc> value."""
    response = client.get(url)
    response.raise_for_status()
    selector = Selector(text=response.text, type="xml")
    return selector.xpath("//*[local-name()='loc']/text()").getall()


def main() -> None:
    with httpx.Client(headers={"User-Agent": UA}, timeout=20, follow_redirects=True) as client:
        robots = Protego.parse(client.get(f"{BASE}/robots.txt").text)
        sitemaps = get_locs(client, f"{BASE}/sitemap-index.xml")

        print("URLs por sitemap:")
        all_urls: list[str] = []
        for sitemap in sitemaps:
            time.sleep(1)
            urls = get_locs(client, sitemap)
            print(f"  {sitemap.rsplit('/', 1)[-1]:38} {len(urls):>5}")
            all_urls.extend(urls)

    unique = sorted(set(all_urls))
    print(f"\nTotal: {len(all_urls)}  |  Únicas: {len(unique)}")

    blocked = [u for u in unique if not robots.can_fetch(u, UA)]
    print(f"\nBloqueadas por robots.txt: {len(blocked)}")
    for url in blocked[:10]:
        print(f"  {url}")

    print("\nURLs con patrones de ruido:")
    for pattern in NOISE_PATTERNS:
        hits = [u for u in unique if pattern in u.lower()]
        example = hits[0] if hits else "-"
        print(f"  {pattern:12} {len(hits):>4}   ej: {example}")

    print("\nURLs por sección (primeros 3 niveles de la ruta):")
    sections = Counter("/".join(urlparse(u).path.strip("/").split("/")[:3]) for u in unique)
    for section, count in sections.most_common(25):
        print(f"  {count:>4}  {section}")

    OUTPUT.write_text("\n".join(unique), encoding="utf-8")
    print(f"\nLista completa guardada en {OUTPUT}")


if __name__ == "__main__":
    main()

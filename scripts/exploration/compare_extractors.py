"""Exploration: compare extraction methods on one raw page."""

import json
import sys
from pathlib import Path

import trafilatura
from parsel import Selector

RAW = Path("data/raw")
VISIBLE_TEXT = (
    "//body//text()[not(ancestor::script) and not(ancestor::style) and not(ancestor::noscript)"
    " and not(ancestor::header) and not(ancestor::footer) and not(ancestor::nav)]"
)


def dom_text(html: str) -> str:
    texts = Selector(text=html).xpath(VISIBLE_TEXT).getall()
    return "\n".join(t.strip() for t in texts if t.strip())


def load_html(url: str) -> str:
    with (RAW / "manifest.jsonl").open(encoding="utf-8") as manifest:
        for line in manifest:
            record = json.loads(line)
            if record["url"] == url:
                return (RAW / record["raw_path"]).read_text(encoding="utf-8")
    raise SystemExit("URL no encontrada en el manifiesto")


def main(url: str, keyword: str) -> None:
    html = load_html(url)
    results = {
        "trafilatura": trafilatura.extract(html, output_format="markdown", include_tables=True)
        or "",
        "trafilatura_recall": trafilatura.extract(
            html, output_format="markdown", include_tables=True, favor_recall=True
        )
        or "",
        "dom_text": dom_text(html),
    }
    for name, text in results.items():
        found = keyword.lower() in text.lower()
        print(
            f"{name:20} {len(text):>7} caracteres   contiene {keyword!r}: {'SÍ' if found else 'no'}"
        )
    print(f"\nInicio del texto de dom_text:\n{results['dom_text'][:600]}")


if __name__ == "__main__":
    main(sys.argv[1].strip(), sys.argv[2].strip())

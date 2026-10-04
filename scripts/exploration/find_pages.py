"""Exploración: encuentra páginas limpias cuyo título o texto
   contenga una palabra clave (para construir el conjunto de referencia)."""

import json
import sys
from pathlib import Path

keyword = sys.argv[1].strip().lower()
with Path("data/clean/pages.jsonl").open(encoding="utf-8") as f:
    pages = [json.loads(line) for line in f]

hits = [
    (page["text"].lower().count(keyword), page)
    for page in pages
    if keyword in page["title"].lower() or keyword in page["text"].lower()
]
for count, page in sorted(hits, key=lambda h: h[0], reverse=True)[:15]:
    print(f"{count:>3}  {page['title'][:50]:50}  {page['url']}")

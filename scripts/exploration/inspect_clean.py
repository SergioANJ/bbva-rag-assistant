"""inspeccionar las páginas limpias para ajustar la limpieza entre páginas (paso B)"""

import json
from collections import Counter, defaultdict
from pathlib import Path

PAGES = Path("data/clean/pages.jsonl")


def main() -> None:
    with PAGES.open(encoding="utf-8") as f:
        pages = [json.loads(line) for line in f]
    total = len(pages)

    print("== 5 páginas más largas ==")
    for page in sorted(pages, key=lambda p: p["char_count"], reverse=True)[:5]:
        print(f"{page['char_count']:>7}  {page['url']}")

    print("\n== Páginas con menos de 300 caracteres ==")
    for page in sorted(pages, key=lambda p: p["char_count"]):
        if page["char_count"] >= 300:
            break
        print(f"{page['char_count']:>5}  {page['url']}")
        print(f"       {page['text'][:90]!r}")

    print("\n== Textos duplicados ==")
    groups = defaultdict(list)
    for page in pages:
        groups[page["content_hash"]].append(page["url"])
    for urls in groups.values():
        if len(urls) > 1:
            print(f"{len(urls)} páginas con el mismo texto:")
            for url in urls[:4]:
                print(f"    {url}")

    print("\n== Bloques más repetidos entre páginas ==")
    doc_freq = Counter()
    for page in pages:
        blocks = {b.strip() for b in page["text"].split("\n\n") if b.strip()}
        doc_freq.update(blocks)
    for block, count in doc_freq.most_common(30):
        print(f"{count:>4} ({count / total:5.1%})  {block[:90]!r}")


if __name__ == "__main__":
    main()

"""Exploración: imprime los fragmentos de una página"""

import json
import sys
from pathlib import Path

with Path("data/chunks/chunks.jsonl").open(encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]

target = sys.argv[1].strip()
if target == "--small":
    for chunk in sorted(chunks, key=lambda c: c["char_count"]):
        if chunk["char_count"] >= 100:
            break
        body = chunk["text"].split("\n\n", 1)[-1]
        print(f"{chunk['char_count']:>4}  pos={chunk['position']}  {chunk['url']}")
        print(f"      {body!r}")
else:
    for chunk in chunks:
        if chunk["url"] == target:
            print(f"--- chunk {chunk['position']} ({chunk['char_count']} chars) ---")
            print(chunk["text"], "\n")

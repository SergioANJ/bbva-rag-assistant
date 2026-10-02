"""Exploración: imprime los fragmentos de una página"""

import json
import sys
from pathlib import Path

url = sys.argv[1].strip()
with Path("data/chunks/chunks.jsonl").open(encoding="utf-8") as f:
    for line in f:
        chunk = json.loads(line)
        if chunk["url"] == url:
            print(f"--- chunk {chunk['position']} ({chunk['char_count']} chars) ---")
            print(chunk["text"], "\n")
"""comprueba si una frase vista en el navegador existe en el código HTML
sin procesar de una página"""

import json
import sys
from pathlib import Path

RAW = Path("data/raw")


def main(url: str, phrase: str) -> None:
    with (RAW / "manifest.jsonl").open(encoding="utf-8") as manifest:
        for line in manifest:
            record = json.loads(line)
            if record["url"] != url:
                continue
            html = (RAW / record["raw_path"]).read_text(encoding="utf-8")
            position = html.lower().find(phrase.lower())
            print(f"Archivo: {record['raw_path']} ({len(html)} caracteres)")
            if position == -1:
                print(f"La frase NO aparece en el HTML crudo: {phrase!r}")
            else:
                print(
                    f"La frase aparece. Contexto:\n{html[max(0, position - 400) : position + 300]}"
                )
            return
    print("URL no encontrada en el manifiesto")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""Guarda el código HTML sin procesar de cada página en el disco
y regístralo en un manifiesto JSONL
"""

import hashlib
import json

from bbva_rag.config import get_settings


class RawHtmlPipeline:
    def open_spider(self, spider):
        self.raw_dir = get_settings().data_dir / "raw"
        self.html_dir = self.raw_dir / "html"
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = (self.raw_dir / "manifest.jsonl").open("w", encoding="utf-8")
        self.saved = 0

    def close_spider(self, spider):
        self.manifest.close()
        spider.logger.info(f"RawHtmlPipeline: saved {self.saved} pages in {self.html_dir}")

    def process_item(self, item, spider):
        url_hash = hashlib.sha256(item["url"].encode("utf-8")).hexdigest()[:16]
        html_path = self.html_dir / f"{url_hash}.html"

        html = item.pop("html")
        html_path.write_text(html, encoding="utf-8")

        item["raw_path"] = html_path.relative_to(self.raw_dir).as_posix()
        item["html_size"] = len(html)
        item["redirected"] = item["url"] != item["requested_url"]

        self.manifest.write(json.dumps(item, ensure_ascii=False) + "\n")
        self.saved += 1
        return item

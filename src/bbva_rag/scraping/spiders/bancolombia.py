"""Un rastreador web que explora las páginas públicas de Bancolombia
que aparecen en su mapa del sitio
"""

from datetime import UTC, datetime

from scrapy.spiders import SitemapSpider

from bbva_rag.config import get_settings
from bbva_rag.scraping.urls import canonicalize_url, is_excluded, is_soft_404

cfg = get_settings()


class BancolombiaSpider(SitemapSpider):
    name = "bancolombia"
    allowed_domains = cfg.scrape_allowed_domains
    sitemap_urls = [cfg.scrape_sitemap_url]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": cfg.scrape_user_agent,
        "DOWNLOAD_DELAY": cfg.scrape_download_delay,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "CLOSESPIDER_ITEMCOUNT": cfg.scrape_max_pages,
        "HTTPCACHE_ENABLED": cfg.scrape_http_cache,
        "ITEM_PIPELINES": {
            "bbva_rag.scraping.pipelines.RawHtmlPipeline": 300,
        },
    }

    def sitemap_filter(self, entries):
        """Elimine las URL que no estén dentro del alcance antes de que se soliciten"""
        for entry in entries:
            if is_excluded(entry["loc"], cfg.scrape_exclude_patterns):
                self.crawler.stats.inc_value("scope/excluded_by_pattern")
                continue
            yield entry

    def parse(self, response):
        redirect_urls = response.meta.get("redirect_urls", [])
        requested_url = redirect_urls[0] if redirect_urls else response.url

        if is_soft_404(requested_url, response.url, cfg.scrape_soft404_paths):
            self.crawler.stats.inc_value("scope/soft_404")
            self.logger.debug(f"Soft 404 discarded: {requested_url} -> {response.url}")
            return

        yield {
            "url": canonicalize_url(response.url),
            "requested_url": requested_url,
            "status": response.status,
            "title": response.css("title::text").get(default="").strip(),
            "fetched_at": datetime.now(UTC).isoformat(),
            "html": response.text,
        }

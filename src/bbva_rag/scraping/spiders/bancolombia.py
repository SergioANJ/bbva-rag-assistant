"""Un rastreador web que explora las páginas públicas de Bancolombia que aparecen en su mapa del sitio."""

from scrapy.spiders import SitemapSpider

class BancolombiaSpider(SitemapSpider):
    name = "bancolombia"
    allowed_domains = ["www.bancolombia.com"]
    sitemap_urls = ["https://www.bancolombia.com/sitemap-index.xml"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True, # Se descarga el archivo robots.txt y respera las reglas
        "USER_AGENT": (
            "Mozilla/5.0 (compatible; bbva-rag-assistant/0.1; "
            "+https://github.com/SergioANJ/bbva-rag-assistant)"
        ), #la cédula de presentación de nuestro bot
        "DOWNLOAD_DELAY": 1.5, #se espera 1.5 sg, entre peticiones
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1, #1 sola petición por dominio
        "CLOSESPIDER_ITEMCOUNT": 5,
    }

    def parse(self, response):
        yield {
            "url": response.url,
            "status": response.status,
            "title": response.css("title::text").get(default="").strip(),
            "html_size": len(response.text),
        }
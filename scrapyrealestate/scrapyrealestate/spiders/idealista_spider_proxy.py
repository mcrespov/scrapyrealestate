import scrapy
from scrapy.spiders import CrawlSpider
from scrapyrealestate.proxies import get_proxies
from scrapyrealestate.spiders.idealista_spider import IdealistaSpider


class IdealistaProxySpider(CrawlSpider):
    """Variante de la spider de Idealista que enruta por proxies rotatorios.

    Reutiliza el parser de IdealistaSpider (solo cambia el transporte: proxies
    en lugar de Playwright). La lista de proxies se carga en update_settings, no
    al importar el módulo, para no penalizar cada `scrapy crawl`/`scrapy list`.
    """
    name = "idealista_proxy"
    allowed_domains = ["idealista.com"]

    # Reutilizamos el parser de la spider principal.
    parse = IdealistaSpider.parse
    parse_start_url = IdealistaSpider.parse

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'es-ES,es;q=0.9,ca;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        }
    }

    def start_requests(self):
        yield scrapy.Request(f'{self.start_urls}')

    @classmethod
    def update_settings(cls, settings):
        # Solo descargamos la lista de proxies cuando se usa esta spider.
        super().update_settings(settings)
        settings.set('ROTATING_PROXY_LIST', get_proxies(), priority='spider')

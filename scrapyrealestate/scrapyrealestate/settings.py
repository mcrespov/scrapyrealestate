# Ajustes de Scrapy para scrapyrealestate.
# https://docs.scrapy.org/en/latest/topics/settings.html

BOT_NAME = 'scrapyrealestate'

SPIDER_MODULES = ['scrapyrealestate.spiders']
NEWSPIDER_MODULE = 'scrapyrealestate.spiders'

DOWNLOADER_MIDDLEWARES = {
    # scrapy_useragents desactivado: sin USER_AGENT_LIST y sin mantenimiento.
    # El User-Agent lo ponen custom_headers (Playwright) y DEFAULT_REQUEST_HEADERS.
    #'scrapy_useragents.downloadermiddlewares.useragents.UserAgentsMiddleware': 500,
    # Sin ROTATING_PROXY_LIST se autodesactivan; solo los usa idealista_proxy.
    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
}

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
# Chromium en vez de WebKit: aguanta mejor el anti-bot de Idealista/Fotocasa.
PLAYWRIGHT_BROWSER_TYPE = 'chromium'

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 60 * 1000,
    # flags tipicos para Chromium en contenedor
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ],
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60 * 1000

PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 1920, "height": 1080},
    },
}

LOG_LEVEL = 'WARNING'
COOKIES_ENABLED = True
ROBOTSTXT_OBEY = False


def custom_headers(browser_type, playwright_request, scrapy_headers) -> dict:
    # User-Agent que escribe main.py; si aun no existe, uno por defecto.
    try:
        with open("./data/useragent.txt", "r") as file:
            useragent = file.read().strip()
    except FileNotFoundError:
        useragent = ""
    if not useragent:
        useragent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return {
        "User-Agent": useragent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


PLAYWRIGHT_PROCESS_REQUEST_HEADERS = custom_headers

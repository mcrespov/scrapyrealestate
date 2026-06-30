import requests
from lxml.html import fromstring


def get_proxies():
    """Conjunto de proxies HTTPS gratuitos de free-proxy-list.net.

    Lista poco fiable (proxies públicos y efímeros); se usa solo en la spider
    idealista_proxy. Si la descarga falla, devolvemos un conjunto vacío en lugar
    de romper el crawl.
    """
    try:
        response = requests.get('https://free-proxy-list.net/', timeout=10)
        parser = fromstring(response.text)
    except requests.RequestException:
        return set()

    proxies = set()
    for row in parser.xpath('//tbody/tr')[:250]:
        # La columna 7 ("Https") marca con "yes" los proxies que soportan HTTPS.
        if row.xpath('.//td[7][contains(text(),"yes")]'):
            ip = row.xpath('.//td[1]/text()')
            port = row.xpath('.//td[2]/text()')
            if ip and port:
                proxies.add(f"{ip[0]}:{port[0]}")
    return proxies

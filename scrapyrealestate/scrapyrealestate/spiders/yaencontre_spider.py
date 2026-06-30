import logging
import scrapy
from bs4 import BeautifulSoup
from scrapyrealestate.items import ScrapyrealestateItem
from scrapy_playwright.page import PageMethod


class YaencontreSpider(scrapy.Spider):
    name = "yaencontre"
    allowed_domains = ["yaencontre.com"]

    def start_requests(self):
        # yaencontre devuelve 403 a peticiones planas; lo cargamos con Playwright.
        yield scrapy.Request(
            f'{self.start_urls}',
            meta={
                'playwright': True,
                'playwright_page_methods': [
                    PageMethod("wait_for_selector", "article.real-estate-card", timeout=30000),
                ],
            },
            errback=self.on_error,
        )

    def on_error(self, failure):
        logging.error(f'Error al obtener datos de yaencontre.com: {failure.value}')

    def parse(self, response):
        default_url = 'https://www.yaencontre.com'
        soup = BeautifulSoup(response.text, 'lxml')
        # Cada vivienda es un article.real-estate-card.
        flats = soup.find_all("article", {"class": "real-estate-card"})

        # alquiler/venta segun la url
        if 'alquiler' in self.start_urls:
            tipo = 'rent'
        elif 'comprar' in self.start_urls or 'venta' in self.start_urls:
            tipo = 'buy'
        else:
            tipo = ''

        for art in flats:
            link = art.find("a", href=True)
            if link is None:
                continue
            href = link['href']
            title = link.get_text(strip=True)
            try:
                id = href.split('-')[1]
            except IndexError:
                id = ''

            # Municipio, barrio y calle desde el titulo separado por comas:
            #   "Piso en calle Huesca, Castillejos, Madrid"
            parts = [p.strip() for p in title.split(',')]
            town = parts[-1] if parts else ''
            neighbour = ''
            street = ''
            if len(parts) >= 3:
                street = parts[0].split(' en ')[-1].strip()
                neighbour = parts[1]
            elif len(parts) == 2:
                neighbour = parts[0].split(' en ')[-1].strip()

            price_el = art.find(class_="price-wrapper")
            price = price_el.get_text(strip=True) if price_el else ''

            # hab. y m² estan en <span> sin clase: los clasificamos por contenido.
            rooms = m2 = ''
            for sp in art.find_all("span"):
                t = sp.get_text(strip=True)
                tl = t.lower()
                if 'hab' in tl and not rooms:
                    rooms = t
                elif 'm²' in tl and not m2:
                    m2 = t

            items = ScrapyrealestateItem()
            items['id'] = id
            items['title'] = title
            items['price'] = price
            items['rooms'] = rooms
            items['m2'] = m2
            items['floor'] = ''
            items['town'] = town
            items['neighbour'] = neighbour
            items['street'] = street
            items['number'] = ''
            items['type'] = tipo
            items['href'] = (default_url + href) if href.startswith('/') else href
            items['site'] = 'yaencontre'
            yield items

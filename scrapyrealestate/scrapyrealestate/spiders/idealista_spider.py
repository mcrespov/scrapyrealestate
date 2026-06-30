import scrapy, logging
from bs4 import BeautifulSoup
from scrapyrealestate.items import ScrapyrealestateItem
from scrapy_playwright.page import PageMethod


class IdealistaSpider(scrapy.Spider):
    name = "idealista"
    allowed_domains = ["idealista.com"]

    def start_requests(self):
        # DataDome puede tardar; damos margen al wait_for_selector y capturamos el
        # fallo con errback (un try/except no atrapa los errores async de Playwright).
        yield scrapy.Request(
            f'{self.start_urls}',
            meta={
                'playwright': True,
                'playwright_page_methods': [
                    PageMethod("wait_for_selector", 'main.listing-items', timeout=45000),
                ],
            },
            errback=self.on_error,
        )

    def on_error(self, failure):
        logging.error(f'Error al obtener datos de idealista.com: {failure.value}')

    def parse(self, response):
        ids = []
        same_id = False
        items = ScrapyrealestateItem()
        default_url = 'https://idealista.com'
        soup = BeautifulSoup(response.text, 'lxml')
        # Cada vivienda es un div.item-info-container.
        flats = soup.find_all("div", {"class": "item-info-container"})
        # Obtenemos si es alquiler o compra a partir de la url
        if self.start_urls.split('/')[3].split('-')[0] == 'alquiler':
            type = 'rent'
        elif self.start_urls.split('/')[3].split('-')[0] == 'venta':
            type = 'buy'

        # Iteramos por cada vivienda de la página y cogemos los datos
        for nflat in range(len(flats)):
            # Cogemos href, title, price, details
            href = flats[nflat].find(class_="item-link")['href']
            title = flats[nflat].find(class_="item-link").text.strip()
            # Intentamos coger ciudad, barrio y calle
            # En idealista puede haber 4 tipos de título, de los que obtendremos estos datos
            neighbour = ''
            street = ''
            number = ''
            town = ''
            # Piso en Calle de Alcalá, 12, Goya, Madrid (4)
            if len(title.split(',')) == 4:
                town = title.split(',')[-1]
                number = title.split(',')[1]
                neighbour = title.split(',')[2]
                street = title.split(',')[0].split(' en ')[-1]
            # Piso en Calle de Alcalá, Goya, Madrid (3)
            elif len(title.split(',')) == 3:
                town = title.split(',')[-1]
                neighbour = title.split(',')[1]
                street = title.split(',')[0].split(' en ')[-1]
            # Ático en Centro, Madrid (2)
            elif len(title.split(',')) == 2:
                town = title.split(',')[-1]
                neighbour = title.split(',')[0].split(' en ')[-1]
            else:
                street = ''
                neighbour = ''
                if len(town) > 12:
                    town = town.split(' en ')[-1]
                if town[:1] == ' ':
                    town = town[1:]
            try:
                if town[0] == ' ':
                    town = town[1:]
            except:
                pass

            try:
                if ' / ' in town:
                    town = town.split(' / ')[1]
                elif '-' in town:
                    town = town.split('-')[0]
            except:
                pass

            try:
                if neighbour[0] == ' ':
                    neighbour = neighbour[1:]
            except:
                pass
            try:
                if number[0] == ' ':
                    number = number[1:]
            except:
                pass

            price = flats[nflat].find("span", {"class": "item-price h2-simulated"}).text.strip()

            details = flats[nflat].find_all("span", {"class": "item-detail"})
            # Cogemos id
            try:
                id = href.split('/')[2]
                # Si el id ya estaba en la lista, salimos
                for id_ in ids:
                    if id_ == id:
                        same_id = True
                        break
            except:
                id = ''

            # Identificamos cada detalle (habitaciones, m², planta) por su sufijo.
            for d in details[0:3]:
                if d.text.strip()[-4:] == 'hab.':
                    rooms = d.text.strip()
                    continue
                elif d.text.strip()[-2:] == 'm²':
                    m2 = d.text.strip()
                    continue
                elif 'Planta' in d.text.strip() or 'Bajo' in d.text.strip() or 'Sótano' in d.text.strip() or 'Entreplanta' in d.text.strip():
                    floor = d.text.strip()
                    continue
                # Hay pisos sin algún dato; lo dejamos vacío para evitar errores.
                else:
                    if not 'rooms' in locals(): rooms = ''
                    if not 'm2' in locals(): m2 = ''
                    if not 'floor' in locals(): floor = ''

            # Si está activado, pasamos al siguiente ya que repite ids
            if same_id:
                continue
            else:
                items['id'] = id
                items['price'] = price
                items['m2'] = m2
                items['rooms'] = rooms
                try:
                    items['floor'] = floor  # si no, falla en sitios sin pisos (p.ej. cerdaña francesa)
                except:
                    items['floor'] = ''
                items['town'] = town
                items['neighbour'] = neighbour
                items['street'] = street
                items['number'] = number
                items['type'] = type
                items['title'] = title
                items['href'] = default_url + href
                items['site'] = 'idealista'
                ids.append(id)

                yield items

    # Procesamos también la primera página (no solo las paginadas).
    parse_start_url = parse

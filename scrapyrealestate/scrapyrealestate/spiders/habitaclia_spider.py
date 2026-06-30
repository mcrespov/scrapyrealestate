import scrapy, re
from scrapy.spiders import CrawlSpider
from bs4 import BeautifulSoup
from scrapyrealestate.items import ScrapyrealestateItem


class HabitacliaSpider(CrawlSpider):
    name = "habitaclia"
    allowed_domains = ["habitaclia.com"]

    def start_requests(self):
        yield scrapy.Request(f'{self.start_urls}')

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'es-ES,es;q=0.9,ca;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }
    }

    def parse(self, response):
        items = ScrapyrealestateItem()
        soup = BeautifulSoup(response.text, 'lxml')
        # Cada vivienda es un div.list-item.
        flats = soup.find_all("div", {"class": "list-item"})

        # Obtenemos si es alquiler o compra a partir de la url
        if self.start_urls.split('/')[3].split('-')[0] == 'alquiler':
            type = 'rent'
        elif self.start_urls.split('/')[3].split('-')[0] == 'venta':
            type = 'buy'
        else:
            type = ''

        for nflat in range(len(flats)):
            try:
                title = flats[nflat].find("h3", {"class": "list-item-title"}).find("a").text.strip()
            except:
                title = ''
            # Municipio, calle y barrio. Ejemplos de titulo:
            #   "Alquiler Piso Calle de Alcala. Magnifico piso..."
            #   "Madrid - Centro"
            town = ''
            neighbour = ''
            street = ''
            street_ = ''
            number = ''
            # Quitamos el prefijo del tipo de inmueble para quedarnos con la via.
            # El orden importa: las variantes "  en  " van antes que las cortas.
            prefixes = ('Alquiler Piso  en  ', 'Alquiler Apartamento  en  ',
                        'Alquiler Piso  ', 'Alquiler Apartamento  ', 'Alquiler Ático  ',
                        'Alquiler Estudio  ', 'Dúplex  en  ', 'Chalet  en  ',
                        'Casa adosada  ', 'Piso  C/ ', 'Piso  ')
            if len(title.split('.')) > 1:
                head = title.split('.')[0]
                for p in prefixes:
                    if p in title:
                        street_ = head.replace(p, '')
                        break
            if street_:
                street = street_

            town_ = flats[nflat].find("p", {"class": "list-item-location"}).find("span").text.strip()
            if ' - ' in town_:
                if len(town_.split(' - ')) == 2:
                    town = town_.split(' - ')[0]
                    neighbour = town_.split(' - ')[-1]
                elif len(town_.split(' - ')) == 3:
                    town = town_.split(' - ')[0]
                    neighbour = town_.split(' - ')[-1]
            try:
                number = re.findall(r'\d+', street)[0]
            except:
                pass

            # Los anuncios "relacionados" (ady-relationship) marcan el final del listado.
            try:
                over_flat = flats[nflat].find("span", {"class": "ady-relationship"}).text.strip()
            except:
                over_flat = ''

            if over_flat != '':
                break

            link_el = flats[nflat].find("h3", {"class": "list-item-title"})
            link_el = link_el.find("a", href=True) if link_el else None
            if link_el is None:
                continue  # tarjeta sin enlace: la saltamos
            href = link_el['href']

            try:
                price = flats[nflat].find("span", {"class": "font-2"}).text.strip()
            except:
                price = ''

            # El texto de list-item-feature es "<m2>m² - <n> habitaciones - ...".
            feature = ''
            try:
                feature = flats[nflat].find("p", {"class": "list-item-feature"}).text.strip()
            except:
                pass
            try:
                rooms = feature.split('-')[1][1:6]
            except:
                rooms = ''
            try:
                m2 = feature.split('-')[0][:4]
            except:
                m2 = ''

            # habitaclia no expone la planta en el listado; queda vacia.
            floor = ''

            # id sintetico (habitaciones + precio + m2): el listado no trae id real.
            id = ''.join(c for c in rooms if c.isdigit()) + \
                 ''.join(c for c in price if c.isdigit()) + \
                 ''.join(c for c in m2 if c.isdigit())

            items['id'] = id
            items['price'] = price.replace(' ', '') + '/mes'
            items['m2'] = m2
            items['rooms'] = rooms
            items['floor'] = floor
            items['town'] = town
            items['neighbour'] = neighbour
            items['street'] = street
            items['number'] = number
            items['type'] = type
            items['title'] = title
            items['href'] = href
            items['site'] = 'habitaclia'

            yield items

    # Procesamos tambien la primera pagina (no solo las paginadas).
    parse_start_url = parse

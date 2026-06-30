import scrapy
from scrapy.spiders import CrawlSpider
from bs4 import BeautifulSoup
from scrapyrealestate.items import ScrapyrealestateItem


class PisoscomSpider(CrawlSpider):
    name = "pisoscom"
    allowed_domains = ["pisos.com"]

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
        ids = []
        same_id = False
        items = ScrapyrealestateItem()
        default_url = 'https://pisos.com'
        soup = BeautifulSoup(response.text, 'lxml')
        # Cada vivienda es un div.ad-preview__info.
        flats = soup.find_all("div", {"class": "ad-preview__info"})

        # Obtenemos si es alquiler o compra a partir de la url
        if self.start_urls.split('/')[3] == 'alquiler':
            type = 'rent'
        elif self.start_urls.split('/')[3] == 'venta':
            type = 'buy'

        # Iteramos por cada vivienda y extraemos sus datos.
        for nflat in range(len(flats)):
            same_id = False
            title_el = flats[nflat].find(class_="ad-preview__title")
            if title_el is None or not title_el.get('href'):
                continue  # tarjeta sin enlace (p. ej. promo): la saltamos
            href = title_el['href']
            title = title_el.text.strip()
            # Municipio, calle y barrio. Ejemplos de titulo:
            #   "Piso en Chamberi"
            #   "Chamberi (Distrito Chamberi. Madrid)"
            town = ''
            neighbour = ''
            street = ''
            number = ''
            street_ = ''
            if len(title.split(',')) == 2:
                street_ = title.split(',')[0]
                number = title.split(',')[-1]
            elif len(title.split(',')) == 1:
                street_ = title.split(' en ')[-1]
            # Solo lo tomamos como calle si el texto contiene un tipo de via.
            street_keywords = ('calle', 'carrer', 'c.', 'avenida', 'avinguda', 'av.',
                               'plaza', 'plaça', 'via', 'travessera', 'camino', 'cami',
                               'paseo', 'passeig', 'passaje', 'passatge', 'carretera', 'ctra.')
            if any(k in street_.lower() for k in street_keywords):
                street = street_

            town_el = flats[nflat].find(class_="p-sm")
            town_ = town_el.text.strip() if town_el else ''
            if '(' in town_:
                neighbour = town_.split('(')[0][:-1]
                town = town_[town_.find('(') + 1:town_.find(')')]
                if 'Distrito' in town:
                    if '.' in town:
                        town = town.split('.')[-1].split(' ')[1]
                    elif 'Capital' in town:
                        town = town.replace('Capital', '').replace(' ', '')
                elif 'Capital' in town:
                    town = town.replace('Capital', '').replace(' ', '')
            else:
                town = town_
            try:
                if ' - ' in town:
                    town = town.split(' - ')[0]
                elif '-' in town_:
                    town = town.split('-')[0]
            except:
                pass

            try:
                id = href.split('-')[2].split('_')[0]
                # Si el id ya estaba en la lista, salimos
                for id_ in ids:
                    if id_ == id:
                        same_id = True
                        break
            except:
                id = ''

            price_el = flats[nflat].find("span", {"class": "ad-preview__price"})
            price = price_el.text.strip() if price_el else ''

            # Las caracteristicas comparten clase y su orden varia (a veces falta
            # habitaciones, etc.), asi que las clasificamos por contenido.
            rooms = m2 = floor = ''
            for c in flats[nflat].find_all("p", {"class": "ad-preview__char p-sm"}):
                t = c.text.strip()
                tl = t.lower()
                if 'hab' in tl:
                    rooms = t
                elif 'm²' in tl or 'm2' in tl:
                    m2 = t
                elif 'planta' in tl or 'bajo' in tl:
                    floor = t

            # Si esta activado, pasamos al siguiente ya que repite ids
            if same_id:
                continue
            else:
                items['id'] = id
                items['price'] = price
                items['m2'] = m2
                items['rooms'] = rooms
                items['floor'] = floor
                items['town'] = town
                items['neighbour'] = neighbour
                items['street'] = street
                items['number'] = number
                items['type'] = type
                items['title'] = title
                items['href'] = default_url + href
                items['site'] = 'pisoscom'
                ids.append(id)

                yield items

    # Procesamos tambien la primera pagina (no solo las paginadas).
    parse_start_url = parse

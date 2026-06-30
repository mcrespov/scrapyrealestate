#!/usr/bin/python3
import re
import sys, subprocess, telebot, time, os.path, os, logging, urllib.request, urllib.error, json, random
from os import path
from art import *
from fake_useragent import UserAgent


__license__ = "GPL"
__version__ = "3.0.0"

# Bot público por defecto. Se puede sobreescribir en la web de configuración
# o con la variable de entorno TELEGRAM_BOT_TOKEN (ver get_bot_token).
DEFAULT_BOT_TOKEN = '5042109408:AAHBrCsNiuI3lXBEiLjmyxqXapX4h1LHbJs'


def get_bot_token():
    # Prioridad: token de la web (config.json) > variable de entorno > por defecto.
    try:
        token = data.get('telegram_bot_token', '')
    except NameError:
        token = ''
    return token or os.environ.get('TELEGRAM_BOT_TOKEN') or DEFAULT_BOT_TOKEN

# Por si fake-useragent falla.
FALLBACK_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)


def init_logs():
    global logger
    try:
        log_level = data['log_level'].upper()
    except (KeyError, NameError, AttributeError):
        log_level = 'INFO'

    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    log_level = levels.get(log_level, logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s',
                                      "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(ch)

    return logger


def mix_list(original_list):
    # baraja para no empezar siempre por el mismo portal
    shuffled = original_list[:]
    random.shuffle(shuffled)
    return shuffled


def get_config():
    # Sin config.json arrancamos la web para que el usuario lo cree.
    if not os.path.isfile('./data/config.json'):
        if not os.path.exists('data'):
            os.makedirs('data')
        process = init_app_flask()
        get_config_flask(process)
    else:
        with open('./data/config.json') as json_file:
            global data
            data = json.load(json_file)


def check_config():
    tb = telebot.TeleBot(get_bot_token())

    if not path.exists("scrapy.cfg"):
        logger.error("NO SE ENCUENTRA EL FICHERO scrapy.cfg")
        sys.exit()

    # URLs para el mensaje de inicio.
    urls = get_urls(data)
    urls_ok = ''
    urls_ok_count = 0
    for portal in urls:
        for url in urls[portal]:
            if len(url.split('/')) > 2:
                portal_url = url.split('/')[2]
                portal_name = portal_url.split('.')[1]
                urls_ok_count += 1
                urls_ok += f' <a href="{url}">{portal_name}</a>    '

    if data['telegram_chatuserID'] is None:
        logger.error('EL CHAT ID DE TELEGRAM ESTÁ VACÍO')
        sys.exit()

    try:
        if data['start_msg'] == 'True':
            info_message = tb.send_message(
                data['telegram_chatuserID'],
                f"<code>LOADING...</code>\n"
                f"\n"
                f"<code>scrapyrealestate v{__version__}\n</code>"
                f"\n"
                f"<code>REFRESH     <b>{data['time_update']}</b>s</code>\n"
                f"<code>MIN PRICE   <b>{data['min_price']}€</b></code>\n"
                f"<code>MAX PRICE   <b>{data['max_price']}€</b> (0 = NO LIMIT)</code>\n"
                f"<code>URLS        <b>{urls_ok_count}</b>  →   </code>{urls_ok}\n",
                parse_mode='HTML'
            )
        else:
            info_message = tb.send_message(
                data['telegram_chatuserID'],
                f"LOADING... scrapyrealestate v{__version__}\n")
    except telebot.apihelper.ApiTelegramException:
        logger.error('EL CHAT ID DE TELEGRAM NO ES CORRECTO O EL BOT '
                     '@scrapyrealestatebot NO SE HA AÑADIDO BIEN AL CANAL')
        sys.exit()

    logger.info(f"CANAL DE TELEGRAM {info_message.chat.title} VERIFICADO")
    return info_message


def checks():
    if int(data['time_update']) < 300:
        logger.error("TIME UPDATE < 300 (el mínimo es 300 segundos)")
        sys.exit()
    check_config()   # valida la configuración y verifica el canal de Telegram


def check_url(url):
    try:
        url_code = urllib.request.urlopen(url).getcode()
    except (urllib.error.URLError, OSError):
        url_code = 404
    return url_code


def init_app_flask():
    # Devuelve el proceso (o None si el servidor ya estaba arriba) para poder pararlo.
    localhost_code = check_url("http://localhost:8080")
    if localhost_code == 200:
        return None

    python_bin = sys.executable or "python3"
    process = subprocess.Popen([python_bin, "./scrapyrealestate/flask_server.py"])
    return process


def get_config_flask(process):
    # Espera a que la web escriba config.json y para el servidor.
    global data
    while True:
        if os.path.isfile('./data/config.json'):
            try:
                with open('./data/config.json') as json_file:
                    data = json.load(json_file)
                break
            except json.JSONDecodeError:
                # todavía se está escribiendo
                pass
        time.sleep(1)
    if process is not None:
        process.terminate()


def get_urls(data):
    urls = {}

    if data.get('url_idealista', '') == '' and data.get('url_pisoscom', '') == '' \
            and data.get('url_fotocasa', '') == '' and data.get('url_habitaclia', '') == '' \
            and data.get('url_yaencontre', '') == '':
        logger.warning("NO URLS ENTERED (MINIMUM 1 URL)")
        sys.exit()

    start_urls_idealista = data.get('url_idealista', [])
    start_urls_idealista = [url + '?ordenado-por=fecha-publicacion-desc' for url in start_urls_idealista]

    start_urls_pisoscom = data.get('url_pisoscom', [])
    start_urls_pisoscom = [url + 'fecharecientedesde-desc/' for url in start_urls_pisoscom]

    start_urls_fotocasa = data.get('url_fotocasa', [])

    start_urls_habitaclia = data.get('url_habitaclia', [])
    start_urls_habitaclia = [url + '?ordenar=mas_recientes' for url in start_urls_habitaclia]

    start_urls_yaencontre = data.get('url_yaencontre', [])
    start_urls_yaencontre = [url + '/o-recientes' for url in start_urls_yaencontre]

    urls['start_urls_idealista'] = start_urls_idealista
    urls['start_urls_pisoscom'] = start_urls_pisoscom
    urls['start_urls_fotocasa'] = start_urls_fotocasa
    urls['start_urls_habitaclia'] = start_urls_habitaclia
    urls['start_urls_yaencontre'] = start_urls_yaencontre

    return urls


def check_new_flats(json_file_name, scrapy_rs_name, min_price, max_price,
                    tg_chatID, telegram_msg, logger):
    '''Detecta viviendas no vistas (contra data/ids.json) y envía por Telegram
    las que entran en el rango de precio. Dedup 100% local, sin BD.'''
    tb = telebot.TeleBot(get_bot_token())
    new_urls = []

    try:
        with open(json_file_name) as json_file:
            data_json = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        data_json = []

    if len(data_json) == 0:
        logger.warning(f'SIN DATOS EN EL JSON {scrapy_rs_name.upper()}')

    try:
        with open("./data/ids.json", "r") as outfile:
            ids_file = json.load(outfile)
    except (FileNotFoundError, json.JSONDecodeError):
        ids_file = []
    new_ids_file = []

    for flat in data_json:
        try:
            flat_id = int(flat['id'])
        except (KeyError, ValueError, TypeError):
            continue

        price_str = flat.get('price', '')
        href = flat.get('href', '')

        # precio a entero (solo dígitos); si no, dejamos el texto
        try:
            price = int(''.join(char for char in price_str if char.isdigit()))
        except (ValueError, TypeError):
            price = 0
        if price == 0:
            price = price_str

        # m2 a entero para el €/m²
        try:
            m2 = int(''.join(char for char in flat.get('m2', '') if char.isdigit())[:-1])
            m2_tg = f'{m2}m²'
        except (ValueError, TypeError):
            m2 = flat.get('m2', 0) or 0
            m2_tg = f'{m2}m²' if m2 else ''

        if flat_id in ids_file:
            continue
        new_ids_file.append(flat_id)

        # "A consultar": lo damos por visto pero no lo enviamos
        if price in ('Aconsultar', 'A consultar'):
            continue

        try:
            within_range = (int(max_price) >= int(price) >= int(min_price)
                            or (int(max_price) == 0 and int(price) >= int(min_price)))
        except (ValueError, TypeError):
            within_range = False

        if within_range and telegram_msg:
            new_urls.append(href)
            try:
                avg_price_m2 = '%.2f' % (price / float(m2))
            except (ValueError, ZeroDivisionError, TypeError):
                avg_price_m2 = ''
            try:
                tb.send_message(
                    tg_chatID,
                    f"<b>{price_str}</b> [{m2_tg}] → {avg_price_m2}€/m²\n{href}",
                    parse_mode='HTML')
            except telebot.apihelper.ApiTelegramException as e:
                logger.error(f'ERROR ENVIANDO A TELEGRAM: {e}')
            time.sleep(3.05)

    with open("./data/ids.json", "w") as outfile:
        json.dump(ids_file + new_ids_file, outfile)

    # solo a INFO si hay nuevas; si no, a DEBUG
    if new_urls:
        logger.info(f"NUEVAS: {len(new_urls)} | TOTAL: {len(data_json)} -> {new_urls}")
    else:
        logger.debug(f"NUEVAS: 0 | TOTAL: {len(data_json)}")


def run_spider(spider_name, scrapy_log, out_file, start_url):
    # Lista de args (sin shell): las URLs con '?'/'&' no rompen la línea de comandos.
    cmd = ["scrapy", "crawl", "-L", scrapy_log, spider_name,
           "-o", out_file, "-a", f"start_urls={start_url}"]
    subprocess.run(cmd, check=False)


def scrap_realestate(telegram_msg):
    scrapy_rs_name = data['scrapy_rs_name'].replace("-", "_")
    scrapy_log = data['log_level_scrapy'].upper()
    proxy_idealista = data['proxy_idealista']
    out_file = f"./data/{scrapy_rs_name}.json"

    # todas las claves 'url_*' de la config
    urls = []
    for key in data:
        if "url" in key and isinstance(data[key], list):
            urls += data[key]
        elif "url" in key:
            urls.append(data[key])

    urls_mixed = mix_list(urls)

    process = subprocess.run(["scrapy", "list"], capture_output=True)
    if process.returncode != 0:
        logger.error("SPIDERS NOT DETECTED")
        sys.exit()

    for url in urls_mixed:
        if url == '':
            continue

        portal_url = url.split('/')[2]
        portal_name = portal_url.split('.')[1]
        try:
            portal_name_url = portal_url.split('.')[1] + '.' + portal_url.split('.')[2]
        except IndexError:
            portal_name = portal_url
            portal_name_url = ''

        logger.debug(f"SCRAPING PORTAL {portal_name_url} FROM {scrapy_rs_name}...")
        if portal_name_url == 'idealista.com':
            url_last_flats = url + '?ordenado-por=fecha-publicacion-desc'
            if proxy_idealista == 'on':
                logger.debug('IDEALISTA PROXY ACTIVATED')
                run_spider('idealista_proxy', scrapy_log, out_file, url_last_flats)
            else:
                run_spider('idealista', scrapy_log, out_file, url_last_flats)
        elif portal_name_url == 'pisos.com':
            url_last_flats = url + '/fecharecientedesde-desc/'
            run_spider('pisoscom', scrapy_log, out_file, url_last_flats)
        elif portal_name_url == 'fotocasa.es':
            run_spider('fotocasa', scrapy_log, out_file, url)
        elif portal_name_url == 'habitaclia.com':
            url_last_flats = url + '?ordenar=mas_recientes'
            run_spider('habitaclia', scrapy_log, out_file, url_last_flats)
        elif portal_name_url == 'yaencontre.com':
            url_last_flats = url + '/o-recientes'
            run_spider('yaencontre', scrapy_log, out_file, url_last_flats)

        logger.debug(f"CRAWLED {portal_name.upper()}")

    # Scrapy con -o concatena varios crawls en el mismo fichero; unimos las partes ('][').
    logger.debug(f"EDITING {out_file}...")
    try:
        with open(out_file, 'r') as file:
            filedata = file.read()
    except FileNotFoundError:
        logger.warning(f"NO SE GENERÓ {out_file} (NINGÚN RESULTADO)")
        return

    filedata = filedata.replace('\n][', ',')
    filedata = re.sub('\n,\n', '', filedata)
    filedata = re.sub(',\n\n', '', filedata)
    filedata = re.sub(',\n]', ']', filedata)
    with open(out_file, 'w') as file:
        file.write(filedata)

    check_new_flats(out_file,
                    scrapy_rs_name,
                    data['min_price'],
                    data['max_price'],
                    data['telegram_chatuserID'],
                    telegram_msg,
                    logger)


def update_useragent():
    try:
        os.remove('./data/useragent.txt')
    except FileNotFoundError:
        pass
    try:
        ua = UserAgent(platforms='pc', os=['windows', 'macos'])
        useragent = ua.chrome
    except Exception as e:
        logger.warning(f'fake-useragent falló ({e}); usando User-Agent de reserva')
        useragent = FALLBACK_USER_AGENT
    with open('./data/useragent.txt', 'w') as f:
        f.write(useragent)


def init():
    tprint("scrapyrealestate")
    print(f'scrapyrealestate v{__version__}')

    get_config()
    init_logs()
    checks()

    count = 0
    telegram_msg = False
    scrapy_rs_name = data['scrapy_rs_name'].replace("-", "_")
    send_first = data['send_first']

    while True:
        try:
            os.remove(f"./data/{scrapy_rs_name}.json")
        except FileNotFoundError:
            pass

        # renovamos el User-Agent cada 10 ciclos
        if count % 10 == 0:
            logger.debug('Renovando User-Agent')
            update_useragent()

        # send_first envía ya en el primer ciclo; si no, solo a partir del segundo
        if send_first == 'True' or count > 0:
            telegram_msg = True

        scrap_realestate(telegram_msg)

        count += 1
        rndtime = random.randint(3, 40) + int(data['time_update'])
        logger.info(f"SLEEPING {rndtime} SECONDS")
        time.sleep(rndtime)


if __name__ == "__main__":
    init()

# Scrapyrealestate

Rastrea varios portales inmobiliarios y avisa por Telegram de las viviendas
nuevas que cumplen tus criterios.

Corre en bucle: cada X segundos lanza los spiders, compara con lo ya visto y, si
aparece una vivienda nueva dentro de tu rango de precio, la publica en tu canal.

Es una versión refactorizada del proyecto original. Lo más importante que cambia:
ya no usa MongoDB (la deduplicación es local, no se manda nada fuera), todo se
configura en la web (incluido el token de Telegram), las dependencias están
fijadas y los spiders de Fotocasa y Yaencontre se han reescrito.

## Cómo funciona

Rastrea Idealista, Pisos.com, Fotocasa, Habitaclia y Yaencontre. Para saber qué es
nuevo guarda en `data/ids.json` los `id` ya avisados y compara contra ahí; lo que
entra en el rango de precio se manda al canal de Telegram. No hay base de datos ni
telemetría.

## Requisitos

- Docker (lo más cómodo), o Python 3.9+ con `requirements.txt`.
- Un canal de Telegram con el bot añadido como administrador (ver abajo).

## Docker

Imagen publicada en Docker Hub: `mcrespov/scrapyrealestate`.

Ejecutar (Docker descarga la imagen sola la primera vez):

```bash
docker run -d \
  --name scrapyrealestate \
  --restart=always \
  -p 8080:8080 \
  mcrespov/scrapyrealestate:latest
```

El `-p 8080:8080` expone la web de configuración del primer arranque. Los datos
(`config.json`, `ids.json`, `useragent.txt`) son efímeros: viven dentro del
contenedor. Un `docker restart` los conserva, pero si borras o recreas el
contenedor se pierden y tendrás que volver a configurarlo por la web (y el
histórico de avisos empieza de cero). Para una segunda instancia cambia nombre y
puerto (`-p 8081:8080`).

Logs:

```bash
docker logs -f scrapyrealestate
```

## Con docker-compose

El repositorio incluye un `docker-compose.yml` que usa la imagen publicada. Para
levantarlo y pararlo:

```bash
docker compose up -d
docker compose down
```

## Construir desde el código (opcional)

Si en vez de usar la imagen publicada prefieres construirla tú mismo:

```bash
docker build -t scrapyrealestate .
```

Ejecutar:

```bash
docker run -d --name scrapyrealestate --restart=always -p 8080:8080 scrapyrealestate
```

## Sin Docker

Con Python 3.9+ (mejor en un [entorno virtual](https://docs.python.org/es/3/tutorial/venv.html)):

```bash
pip3 install -r scrapyrealestate/requirements.txt
playwright install chromium

cd scrapyrealestate
python3 main.py
```

En segundo plano en Linux: `nohup python3 main.py &` (logs en `nohup.out`).

## Configuración

La primera vez, si no hay `data/config.json`, el programa abre una web de
configuración en `http://localhost:8080/`. Rellénala y guarda: se crea
`data/config.json` y el programa sigue solo. Mientras ese fichero exista no se
vuelve a pedir nada (puedes editarlo a mano).

Las URLs de los portales vienen precumplimentadas con búsquedas de Madrid;
cámbialas por las tuyas antes de guardar.

Parámetros:

- `scrapy_rs_name`: nombre de la instancia.
- `log_level`: nivel de log del script (por defecto `INFO`).
- `log_level_scrapy`: nivel de log de Scrapy (por defecto `WARNING`).
- `time_update`: segundos entre búsquedas (mínimo 300).
- `telegram_chatuserID`: el chat id de tu canal (ver abajo).
- `telegram_bot_token`: token de tu bot de @BotFather. Opcional (ver nota abajo).
- `start_msg`: si es `True`, manda un mensaje al arrancar.
- `min_price` / `max_price`: rango de precio (`max_price = 0` es sin límite).
- `url_idealista` / `url_pisoscom` / `url_fotocasa` / `url_habitaclia` /
  `url_yaencontre`: URLs de búsqueda de cada portal (admite varias).
- `proxy_idealista`: proxies rotatorios para Idealista (`on`); por defecto off.
- `send_first`: si se activa, avisa también de lo que ya hay en el primer ciclo.

El `telegram_bot_token` es opcional: si lo dejas vacío se usa un bot público por
defecto.

### Canal de Telegram y chat id

1. Crea un canal (público o privado).
2. Añade tu bot como administrador con permiso para publicar (créalo con
   [@BotFather](https://t.me/BotFather) y pon su token en el campo
   `telegram_bot_token` de la web). Si el bot no está bien añadido, el programa
   no arranca.
3. Saca el chat id del canal, por ejemplo con [@RawDataBot](https://t.me/RawDataBot).
   Es lo que va en `telegram_chatuserID` (tipo `-1001647968000`).

## Estado de los portales

| Portal     | Estado    | Notas |
|------------|-----------|-------|
| Pisos.com  | Funciona  | HTML estable. |
| Habitaclia | Funciona  | HTML estable. |
| Yaencontre | Funciona  | Se carga con Playwright (devuelve 403 a peticiones planas). |
| Fotocasa   | Funciona  | Playwright + Chromium; el spider lee el JSON embebido de la página, no las clases CSS. |
| Idealista  | No fiable | DataDome bloquea el navegador automatizado en headless. Se probó Chromium, stealth, headful con Xvfb y Playwright parcheado (rebrowser) sin éxito; usarlo de verdad pediría un servicio anti-bot de pago. |

Rastrea con cabeza y respeta el refresco mínimo (300s).

## Probar un spider

`test_spider.sh` lanza un crawl de un portal y muestra cuántas viviendas saca y un
par de ejemplos. Se ejecuta donde está `scrapy.cfg`. En Docker:

```bash
docker exec -it scrapyrealestate bash -c \
  "cd /scrapyrealestate/scrapyrealestate && ./test_spider.sh fotocasa"
```

Spiders: `idealista`, `pisoscom`, `habitaclia`, `fotocasa`, `yaencontre`. Puedes
pasar tu URL como segundo argumento.

## Estructura

```
Dockerfile
docker-compose.yml
README.md
scrapyrealestate/
├── main.py                  # bucle, Telegram y deduplicación local
├── requirements.txt
├── scrapy.cfg
├── test_spider.sh
└── scrapyrealestate/
    ├── settings.py          # Scrapy + Playwright (Chromium)
    ├── items.py
    ├── flask_server.py      # web de configuración del primer arranque
    ├── proxies.py
    ├── templates/
    └── spiders/             # idealista, pisoscom, fotocasa, habitaclia, yaencontre
```

`data/` (ignorada por git) guarda `config.json`, `ids.json` y `useragent.txt`.

## Créditos y licencia

Basado en [mferark/scrapyrealestate](https://github.com/mferark/scrapyrealestate). Licencia GPL.

## Colaborar

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/mcrespov)

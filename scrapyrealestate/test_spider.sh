#!/usr/bin/env bash
#
# test_spider.sh - Prueba end-to-end de un spider concreto.
#
# Lanza un crawl real (scrapy-playwright + Chromium), guarda el resultado en
# ./data/test_<spider>.json y muestra un resumen: numero de viviendas y muestra.
#
# Ejecutar desde la carpeta que contiene scrapy.cfg (esta misma).
# En Docker: docker exec -it <contenedor> bash -c "cd /scrapyrealestate/scrapyrealestate && ./test_spider.sh <spider> [url]"
#
# Uso: ./test_spider.sh <spider> [url]
#   idealista | pisoscom | habitaclia | fotocasa | yaencontre

set -u

SPIDER="${1:-fotocasa}"

case "$SPIDER" in
  idealista)  DEFAULT_URL="https://www.idealista.com/alquiler-viviendas/madrid-madrid/?ordenado-por=fecha-publicacion-desc" ;;
  pisoscom)   DEFAULT_URL="https://www.pisos.com/venta/pisos-madrid/fecharecientedesde-desc/" ;;
  habitaclia) DEFAULT_URL="https://www.habitaclia.com/alquiler-madrid.htm?ordenar=mas_recientes" ;;
  fotocasa)   DEFAULT_URL="https://www.fotocasa.es/es/alquiler/viviendas/madrid-capital/todas-las-zonas/l" ;;
  yaencontre) DEFAULT_URL="https://www.yaencontre.com/alquiler/pisos/madrid/o-recientes" ;;
  *) echo "Spider desconocido: $SPIDER (usa: idealista | pisoscom | habitaclia | fotocasa | yaencontre)"; exit 1 ;;
esac

URL="${2:-$DEFAULT_URL}"
OUT="./data/test_${SPIDER}.json"

if [ ! -f "scrapy.cfg" ]; then
  echo "ERROR: ejecuta este script desde la carpeta que contiene scrapy.cfg."
  exit 1
fi

# El settings.py lee ./data/useragent.txt; lo creamos si no existe.
mkdir -p ./data
if [ ! -s "./data/useragent.txt" ]; then
  echo "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" > ./data/useragent.txt
fi

rm -f "$OUT"

echo "=================================================================="
echo " Spider : $SPIDER"
echo " URL    : $URL"
echo " Salida : $OUT"
echo "=================================================================="
echo ">> Lanzando crawl (logs en nivel INFO)..."
echo

scrapy crawl -L INFO "$SPIDER" -o "$OUT" -a start_urls="$URL"
STATUS=$?

echo
echo "=================================================================="
if [ $STATUS -ne 0 ]; then
  echo "El comando scrapy termino con codigo $STATUS."
fi

if [ ! -f "$OUT" ]; then
  echo "RESULTADO: no se genero $OUT -> 0 viviendas (probable bloqueo o selector roto)."
  exit 1
fi

python3 - "$OUT" <<'PYEOF'
import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path, encoding="utf-8"))
except Exception as e:
    print(f"RESULTADO: el JSON no se pudo leer ({e}). Revisa el log de arriba.")
    sys.exit(1)
print(f"RESULTADO: {len(data)} viviendas extraidas.")
for flat in data[:2]:
    print("-" * 50)
    for k in ("id", "price", "m2", "rooms", "town", "neighbour", "href", "site"):
        if k in flat:
            print(f"  {k:9}: {flat[k]}")
PYEOF
echo "=================================================================="

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="scrapyrealestate" \
      org.opencontainers.image.description="Scraping de portales inmobiliarios con avisos por Telegram" \
      org.opencontainers.image.licenses="GPL-3.0"

# Entorno: salida sin buffer, sin .pyc, pip sin cache y zona horaria.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Europe/Madrid

# Dependencias del sistema minimas.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /scrapyrealestate/scrapyrealestate

# Instalamos primero las dependencias (mejor uso de la cache de capas).
COPY scrapyrealestate/requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Navegador de Playwright. Solo Chromium (es el que usan los spiders).
RUN playwright install --with-deps chromium

# Copiamos la aplicacion.
COPY scrapyrealestate/ ./

EXPOSE 8080

CMD ["python", "main.py"]

FROM python:3.11-slim

# libgomp1 (xgboost en runtime) y git (para instalar iqoptionapi desde GitHub)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# iqoptionapi (no oficial): se instala desde GitHub (la versión de PyPI está
# rota). Se permite que falle para no romper el build; si no se instala, el
# servicio detecta la ausencia y opera en modo simulación.
RUN pip install --no-cache-dir "git+https://github.com/iqoptionapi/iqoptionapi.git" \
    || echo "iqoptionapi no instalado: modo simulación disponible"

# httpx 0.27.2 es la última versión compatible con openai==1.30.1.
# httpx>=0.28 eliminó el parámetro 'proxies' que openai 1.30.x usa internamente.
RUN pip install --no-cache-dir "httpx==0.27.2"

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

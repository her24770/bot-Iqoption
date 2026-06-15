#!/bin/sh
set -e

echo "==> Esperando a PostgreSQL..."
python - <<'PY'
import os, time
import psycopg2

url = os.environ.get("DATABASE_URL", "")
for intento in range(60):
    try:
        psycopg2.connect(url).close()
        print("==> PostgreSQL disponible")
        break
    except Exception as exc:
        print(f"   ... base de datos no lista ({exc}); reintentando")
        time.sleep(2)
else:
    print("==> No se pudo conectar a PostgreSQL; se continuará y la app intentará crear tablas")
PY

echo "==> Ejecutando migraciones de Alembic..."
alembic upgrade head || echo "==> Alembic falló; la app usará create_all como respaldo"

echo "==> Iniciando Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT:-8000}"

# IQBot — Bot de trading IQ Option + Dashboard

Bot de trading automatizado para IQ Option con dashboard de administración web.
Dos componentes orquestados con un solo `docker-compose.yml`:

- **iqbot-core** — bot Python (FastAPI) que analiza el mercado, detecta patrones,
  puntúa señales con XGBoost, consulta a GPT-4o mini y ejecuta operaciones.
- **iqbot-dashboard** — interfaz React para controlar el bot, ver resultados en
  tiempo real y ajustar parámetros sin reiniciar.

> ⚠️ Modo simulación: si no configuras credenciales de IQ Option (o la librería
> `iqoptionapi` no está disponible), el bot arranca automáticamente en **modo
> simulación**: genera velas, balance y resultados sintéticos para que TODO el
> stack funcione localmente de extremo a extremo. En tu servidor, al poner las
> credenciales reales, se conecta a IQ Option de verdad.

---

## Arranque local (Docker)

```bash
# 1. Copia las variables de entorno y edítalas
cp .env.example .env

# 2. Levanta todo el stack
docker compose up --build
```

Servicios disponibles:

| Servicio    | URL                       |
|-------------|---------------------------|
| Dashboard   | http://localhost:5173     |
| API (docs)  | http://localhost:8000/docs|
| PostgreSQL  | localhost:5432 (interno)  |
| Redis       | interno                   |

### Login del dashboard

El usuario admin se crea automáticamente al arrancar usando
`DASHBOARD_EMAIL` y `DASHBOARD_PASSWORD` del `.env`.

Por defecto: `admin@tudominio.com` / `admin123` (cámbialo).

---

## Variables de entorno

Todas se documentan en [`.env.example`](.env.example). Las más importantes:

- `IQOPTION_EMAIL` / `IQOPTION_PASSWORD` — vacías = simulación.
- `OPENAI_API_KEY` — vacía = se omite el paso de GPT.
- `DB_PASSWORD` **debe coincidir** con la contraseña dentro de `DATABASE_URL`.
- `JWT_SECRET` — cadena larga y aleatoria para firmar los tokens.
- `VITE_API_URL` — URL del backend que usa el navegador (build del frontend).

---

## Cómo funciona el bot

Cada 5 minutos (APScheduler), si el bot está activo:

1. Verifica el límite de operaciones por hora.
2. Obtiene las últimas 50 velas de 5 min.
3. Calcula indicadores: RSI(14), EMA(9/21), Bollinger(20,2), volumen.
4. Detecta los 3 patrones (RSI Reversal, EMA Cross, BB Squeeze).
5. Puntúa la señal con XGBoost; descarta si está por debajo del umbral.
6. Pide la decisión final a GPT-4o mini (CALL/PUT/SKIP).
7. Aplica delays aleatorios (anti-detección) y ejecuta.
8. Guarda en PostgreSQL + Redis y emite log por WebSocket.
9. Al vencer la opción, resuelve el resultado y aplica la lógica de
   pérdidas consecutivas (detiene el bot si supera el límite).

El modelo XGBoost se entrena al iniciar (data de yfinance o sintética si no hay
red) y se reentrena automáticamente cada N operaciones. Se persiste en el volumen
`iqbot_model` (`/app/data/model.pkl`).

---

## Estructura

```
.
├── docker-compose.yml
├── .env.example
├── iqbot-core/        # Backend FastAPI + bot
└── iqbot-dashboard/   # Frontend React + Vite + Tailwind
```

---

## Comandos útiles

```bash
# Ver logs del backend
docker compose logs -f iqbot-core

# Reconstruir solo un servicio
docker compose up --build iqbot-core

# Detener y borrar volúmenes (resetea BD y modelo)
docker compose down -v
```

---

## API principal

| Método | Ruta                        | Descripción                       |
|--------|-----------------------------|-----------------------------------|
| POST   | `/auth/login`               | Login → JWT                       |
| GET    | `/auth/me`                  | Usuario autenticado               |
| POST   | `/bot/start` · `/bot/stop`  | Encender / apagar el bot          |
| GET    | `/bot/status`               | Estado + balance + ops hora       |
| GET/PUT| `/config`                   | Configuración en vivo             |
| GET    | `/operaciones`              | Historial paginado                |
| GET    | `/operaciones/stats`        | Win rate, P&L, gráfica, patrones  |
| GET    | `/operaciones/export/csv`   | Exportar historial                |
| WS     | `/ws/logs?token=...`        | Logs en tiempo real               |

---

## Aviso

Este software opera con dinero real cuando se configura en modo `real`. El
trading de opciones binarias conlleva alto riesgo. Úsalo bajo tu propia
responsabilidad y prueba siempre primero en modo `demo`/simulación.

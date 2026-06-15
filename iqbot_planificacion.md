# IQBot — Planificación Técnica Completa
> Bot de trading automatizado para IQ Option con dashboard de administración web
> Documento para Claude Code — leer completo antes de escribir cualquier línea de código

---

## Visión

Dos componentes en uno:
- **iqbot-core** — bot Python que analiza el mercado, detecta patrones y ejecuta operaciones en IQ Option de forma autónoma
- **iqbot-dashboard** — interfaz web React para controlar el bot, ver resultados en tiempo real y ajustar parámetros sin reiniciar nada

---

## Repositorios

| Repo | Descripción | Tecnología |
|------|-------------|------------|
| `iqbot-core` | Bot + API REST de control | Python + FastAPI |
| `iqbot-dashboard` | Dashboard de administración | React + Vite + TailwindCSS |

Ambos repos viven juntos bajo un solo `docker-compose.yml` en la raíz.

---

## Stack Tecnológico

### Backend (iqbot-core)
| Tecnología | Uso |
|------------|-----|
| Python 3.11+ | Lenguaje base |
| FastAPI | API REST + WebSocket para logs en tiempo real |
| iqoptionapi | Conexión con IQ Option (no oficial) |
| pandas-ta | Indicadores técnicos (RSI, EMA, Bollinger Bands) |
| xgboost | Modelo ML para scoring de señales |
| scikit-learn | Preprocessing + métricas de reentrenamiento |
| yfinance | Data histórica para inicializar el modelo |
| openai | GPT-4o mini para decisión final con contexto |
| SQLAlchemy 2.x | ORM |
| Alembic | Migraciones de BD |
| PostgreSQL 15 | Historial de operaciones + configuración |
| Redis 7 | Estado del bot en tiempo real + rate limiting |
| APScheduler | Análisis cada 5 min + reentrenamiento automático |
| Pydantic v2 | Validación de datos |
| python-jose | JWT para autenticación del dashboard |
| passlib | Hash de contraseñas |

### Frontend (iqbot-dashboard)
| Tecnología | Uso |
|------------|-----|
| React 18 + Vite | Framework UI |
| TailwindCSS | Estilos |
| Recharts | Gráfica de rendimiento acumulado |
| Axios | Llamadas a la API |
| WebSocket nativo | Logs en tiempo real |

---

## Arquitectura de Carpetas

### Backend (`iqbot-core/`)
```
iqbot-core/
├── app/
│   ├── main.py                  # FastAPI app, routers, CORS, WebSocket
│   ├── config.py                # Settings desde .env
│   ├── database.py              # SQLAlchemy engine + session
│   ├── redis_client.py          # Cliente Redis
│   │
│   ├── models/
│   │   ├── operacion.py         # Historial de operaciones
│   │   ├── configuracion.py     # Configuración persistente del bot
│   │   └── usuario.py           # Usuario del dashboard (login)
│   │
│   ├── schemas/
│   │   ├── operacion.py
│   │   ├── configuracion.py
│   │   └── auth.py
│   │
│   ├── routers/
│   │   ├── auth.py              # POST /auth/login, GET /auth/me
│   │   ├── bot.py               # POST /bot/start, POST /bot/stop, GET /bot/status
│   │   ├── config.py            # GET/PUT /config (parámetros en vivo)
│   │   ├── operaciones.py       # GET /operaciones (historial + métricas)
│   │   └── ws.py                # WebSocket /ws/logs
│   │
│   ├── services/
│   │   ├── iqoption_service.py  # Conexión y ejecución en IQ Option
│   │   ├── indicator_service.py # Cálculo de RSI, EMA, Bollinger
│   │   ├── pattern_service.py   # Detección de los 3 patrones
│   │   ├── gpt_service.py       # Llamada a GPT-4o mini para decisión final
│   │   ├── ml_service.py        # XGBoost: scoring + reentrenamiento
│   │   ├── bot_engine.py        # Loop principal del bot (APScheduler)
│   │   └── human_behavior.py    # Delays aleatorios, límites, anti-detección
│   │
│   └── utils/
│       ├── logger.py            # Logger con broadcast a WebSocket
│       └── responses.py         # Respuestas estándar de error
│
├── migrations/
│   └── versions/
├── .env
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

### Frontend (`iqbot-dashboard/`)
```
iqbot-dashboard/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── pages/
│   │   ├── Login.jsx
│   │   └── Dashboard.jsx
│   ├── components/
│   │   ├── BotControls.jsx      # Botón encender/apagar + modo demo/real
│   │   ├── StatusCard.jsx       # Estado actual del bot
│   │   ├── BalanceCard.jsx      # Balance en tiempo real
│   │   ├── StatsCards.jsx       # Win rate, total ops, P&L
│   │   ├── OperacionesTable.jsx # Historial de operaciones
│   │   ├── RendimientoChart.jsx # Gráfica acumulada (Recharts)
│   │   ├── PatternStats.jsx     # Win rate por patrón
│   │   ├── ConfigPanel.jsx      # Panel de parámetros en vivo
│   │   └── LogsPanel.jsx        # Logs en tiempo real (WebSocket)
│   ├── services/
│   │   ├── api.js               # Axios base + interceptores JWT
│   │   └── ws.js                # Cliente WebSocket para logs
│   ├── context/
│   │   └── AuthContext.jsx
│   └── hooks/
│       ├── useBot.js
│       └── useLogs.js
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

---

## Base de Datos (PostgreSQL)

```sql
-- Configuración del bot (una sola fila, siempre id=1)
configuracion
├── id (integer PK, default 1)
├── par (varchar, default 'EURUSD')
├── modo (varchar: 'demo' | 'real', default 'demo')
├── activo (boolean, default false)
├── umbral_confianza (float, default 0.70)
├── max_ops_por_hora (integer, default 6)
├── monto_porcentaje_balance (float, default 0.02)  -- 2% del balance por op
├── perdidas_consecutivas_limite (integer, default 3)
├── reentrenar_cada_n_ops (integer, default 100)
└── updated_at (timestamp)

-- Historial de operaciones
operaciones
├── id (uuid PK)
├── par (varchar)
├── direccion (varchar: 'CALL' | 'PUT')
├── monto (float)
├── resultado (varchar: 'WIN' | 'LOSE' | 'PENDING')
├── ganancia (float)
├── patron_activado (varchar)        -- qué patrón disparó la operación
├── confianza_ml (float)             -- score del modelo XGBoost
├── decision_gpt (varchar)           -- CALL | PUT | SKIP
├── modo (varchar: 'demo' | 'real')
├── indicadores_snapshot (JSONB)     -- RSI, EMA, BB al momento de operar
├── created_at (timestamp)
└── expires_at (timestamp)           -- cuando vence la opción

-- Usuario del dashboard
usuarios
├── id (uuid PK)
├── email (varchar unique)
├── password_hash (varchar)
└── created_at (timestamp)
```

### Redis
```
bot:estado           → { activo, par, modo, ultima_operacion, ops_esta_hora }
bot:config           → espejo de la tabla configuracion (lectura rápida)
bot:perdidas_streak  → contador de pérdidas consecutivas (se resetea con WIN)
rate_limit:{session} → contador de ops esta hora, TTL 1h
logs:stream          → lista de los últimos 200 logs (para reconexión WS)
```

---

## Lógica del Bot Engine

### Loop principal (APScheduler, cada 5 minutos)

```
¿Bot activo? No → salir
      ↓
¿Se alcanzó max_ops_por_hora? Sí → loggear "límite alcanzado" y salir
      ↓
Obtener velas en tiempo real de IQ Option (últimas 50 velas de 5min)
      ↓
Calcular indicadores:
  - RSI(14)
  - EMA(9) y EMA(21)
  - Bollinger Bands(20, 2)
  - Volumen promedio(20)
      ↓
Detectar patrones (ver sección Patrones)
      ↓
¿Algún patrón activo? No → loggear "sin señal" y salir
      ↓
XGBoost scoring con [RSI, EMA_diff, BB_position, volumen_ratio, patron_id]
      ↓
¿Score > umbral_confianza? No → loggear "confianza insuficiente: X%" y salir
      ↓
Llamar a GPT-4o mini con contexto completo (ver sección GPT)
      ↓
¿GPT dice SKIP? → loggear "GPT recomienda no operar" y salir
      ↓
Calcular monto = balance_actual * monto_porcentaje_balance
      ↓
human_behavior.delay() → esperar entre 2.5 y 7 segundos aleatorios
      ↓
Ejecutar operación en IQ Option
      ↓
Guardar en PostgreSQL + actualizar Redis
      ↓
Broadcast log a WebSocket
```

### Seguridad por pérdidas consecutivas
```
Después de cada operación:
  Si resultado == LOSE:
    incrementar bot:perdidas_streak
    Si streak >= perdidas_consecutivas_limite:
      desactivar bot (activo = false)
      loggear "Bot detenido: X pérdidas consecutivas"
      broadcast alerta al dashboard
  Si resultado == WIN:
    resetear bot:perdidas_streak a 0
```

---

## Los 3 Patrones de Trading

### Patrón 1 — RSI Reversal + Vela Envolvente
```
CALL: RSI < 30 AND vela actual cierra > vela anterior (envolvente alcista)
PUT:  RSI > 70 AND vela actual cierra < vela anterior (envolvente bajista)
```

### Patrón 2 — Cruce de EMAs con Volumen
```
CALL: EMA9 cruza hacia arriba EMA21 AND volumen > promedio_20_velas * 1.2
PUT:  EMA9 cruza hacia abajo EMA21  AND volumen > promedio_20_velas * 1.2
```

### Patrón 3 — Bollinger Squeeze
```
CALL: precio toca banda inferior AND RSI entre 30 y 50
PUT:  precio toca banda superior AND RSI entre 50 y 70
```

**Señal válida:** Al menos 1 patrón activo. El XGBoost pondera cuáles combinaciones históricamente tienen mejor win rate.

---

## Integración GPT-4o mini

### Prompt al modelo
```python
system = """
Eres un analista de trading especializado en opciones binarias forex de 5 minutos.
Recibes datos técnicos de mercado y debes decidir: CALL, PUT o SKIP.
Responde ÚNICAMENTE con un JSON: {"decision": "CALL"|"PUT"|"SKIP", "razon": "string corto"}
No agregues nada más, sin markdown, sin explicaciones extra.
"""

user = f"""
Par: {par}
Timeframe: 5 minutos
Timestamp: {timestamp}

Indicadores actuales:
- RSI(14): {rsi}
- EMA9: {ema9} | EMA21: {ema21} | Diferencia: {ema_diff}
- Bollinger: inferior={bb_lower}, media={bb_mid}, superior={bb_upper}
- Precio actual: {precio}
- Volumen relativo: {vol_ratio}x del promedio

Patrones detectados: {patrones_activos}
Score XGBoost: {score}% de confianza

Win rate histórico de estos patrones en mis últimas {n_ops} operaciones: {win_rate_historico}%

¿Ejecuto operación?
"""
```

---

## Anti-Detección (human_behavior.py)

```python
import random, time

def delay_antes_de_operar():
    """Simula tiempo de 'análisis humano' antes de ejecutar"""
    time.sleep(random.uniform(2.5, 7.0))

def delay_entre_sesiones():
    """Variación aleatoria en el intervalo del scheduler"""
    # El scheduler corre cada 5 min pero con ±30 segundos de jitter
    return random.uniform(-30, 30)

MAX_OPS_POR_HORA = configuracion.max_ops_por_hora  # configurable
# Nunca operar exactamente en :00 de cada hora (patrón de bot obvio)
# Si el análisis cae en minuto :00, agregar 15-45 segundos extra
```

---

## API REST (iqbot-core)

### Auth
```
POST  /auth/login          → { email, password } → JWT token
GET   /auth/me             → info del usuario autenticado
```

### Bot Control
```
POST  /bot/start           → activa el bot
POST  /bot/stop            → pausa el bot
GET   /bot/status          → estado actual + balance + ops esta hora
```

### Configuración (cambios en vivo, sin reiniciar)
```
GET   /config              → configuración actual
PUT   /config              → actualizar cualquier parámetro
      Body: {
        par?, modo?, umbral_confianza?, max_ops_por_hora?,
        monto_porcentaje_balance?, perdidas_consecutivas_limite?,
        reentrenar_cada_n_ops?
      }
```

### Operaciones
```
GET   /operaciones         → historial con paginación
      ?page=1&limit=20&modo=demo|real
GET   /operaciones/stats   → win rate total, por patrón, P&L, gráfica
GET   /operaciones/export/csv → exportar historial
```

### WebSocket
```
WS    /ws/logs             → stream de logs en tiempo real
      Autenticado con JWT en query param: /ws/logs?token=xxx
      Formato mensaje: { timestamp, level, message }
```

### Respuesta de error estándar
```json
{
  "error": true,
  "code": "BOT_ALREADY_RUNNING",
  "message": "El bot ya está activo"
}
```

---

## Dashboard — Secciones y Funcionalidad

### Header
- Logo "IQBot" + indicador de estado (verde=activo, rojo=detenido, amarillo=analizando)
- Modo actual: badge DEMO o REAL
- Botón logout

### Sección 1 — Control Principal
- Toggle grande ON/OFF para activar/pausar el bot
- Switch DEMO ↔ REAL (con confirmación modal antes de cambiar a REAL)
- Balance actual en tiempo real

### Sección 2 — Stats Cards (4 cards)
- Win Rate total (%)
- Total operaciones
- P&L acumulado ($)
- Operaciones esta hora / máximo

### Sección 3 — Gráfica de Rendimiento
- Recharts LineChart con P&L acumulado por día
- Filtro: últimos 7 días / 30 días / todo

### Sección 4 — Win Rate por Patrón
- 3 barras: Patrón RSI Reversal | Patrón EMA Cross | Patrón BB Squeeze
- Muestra cuál patrón está siendo más efectivo

### Sección 5 — Configuración en Vivo
Panel colapsable con todos los parámetros editables:
- Par de divisas (dropdown: EUR/USD, GBP/USD, USD/JPY, AUD/USD)
- Umbral de confianza mínimo (slider 50%–95%)
- Máx operaciones por hora (input numérico)
- % del balance por operación (slider 1%–10%)
- Límite de pérdidas consecutivas antes de parar (input numérico)
- Reentrenar modelo cada N operaciones (input numérico)
- Botón "Guardar cambios" → aplica inmediatamente sin reiniciar

### Sección 6 — Historial de Operaciones
Tabla con columnas:
- Fecha/hora | Par | Dirección | Monto | Resultado | Ganancia | Patrón | Confianza ML | Decisión GPT

### Sección 7 — Logs en Tiempo Real
- Terminal oscuro con scroll automático
- Logs con colores por nivel: INFO (blanco), WARN (amarillo), ERROR (rojo), SUCCESS (verde)
- Botón para limpiar pantalla (no borra de Redis)
- Reconexión automática si cae el WebSocket

---

## Reentrenamiento del Modelo (ML)

```
Cada N operaciones (configurable, default 100):
  1. Cargar todas las operaciones de la BD con resultado WIN/LOSE
  2. Features: [rsi, ema_diff, bb_position, vol_ratio, patron_id, hora_del_dia]
  3. Label: 1=WIN, 0=LOSE
  4. Reentrenar XGBoost con los nuevos datos
  5. Guardar modelo en disco (model.pkl)
  6. Loggear: "Modelo reentrenado con X operaciones. Accuracy: Y%"
  7. El nuevo modelo entra en efecto inmediatamente
```

El modelo inicial (antes de tener historial propio) usa data histórica de yfinance para EUR/USD de los últimos 12 meses con los mismos features e indicadores.

---

## Variables de Entorno (.env)

```env
# IQ Option
IQOPTION_EMAIL=tu@email.com
IQOPTION_PASSWORD=tu_password

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Base de datos
DATABASE_URL=postgresql://iqbot:password@iqbot-db:5432/iqbot_db

# Redis
REDIS_URL=redis://iqbot-redis:6379

# Auth dashboard
JWT_SECRET=cadena-larga-y-aleatoria-aqui
JWT_EXPIRE_HOURS=24
DASHBOARD_EMAIL=admin@tudominio.com
DASHBOARD_PASSWORD=tu_password_del_dashboard

# App
APP_ENV=production
APP_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://tu-server-ip
```

---

## Docker Compose

```yaml
# docker-compose.yml (raíz del proyecto)
services:

  iqbot-core:
    build: ./iqbot-core
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      IQOPTION_EMAIL: ${IQOPTION_EMAIL}
      IQOPTION_PASSWORD: ${IQOPTION_PASSWORD}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OPENAI_MODEL: ${OPENAI_MODEL}
      JWT_SECRET: ${JWT_SECRET}
      JWT_EXPIRE_HOURS: ${JWT_EXPIRE_HOURS}
      DASHBOARD_EMAIL: ${DASHBOARD_EMAIL}
      DASHBOARD_PASSWORD: ${DASHBOARD_PASSWORD}
      CORS_ORIGINS: ${CORS_ORIGINS}
    depends_on:
      - iqbot-db
      - iqbot-redis
    restart: unless-stopped

  iqbot-dashboard:
    build: ./iqbot-dashboard
    ports:
      - "5173:80"
    depends_on:
      - iqbot-core
    restart: unless-stopped

  iqbot-db:
    image: postgres:15
    environment:
      POSTGRES_DB: iqbot_db
      POSTGRES_USER: iqbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - iqbot_pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  iqbot-redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  iqbot_pgdata:
```

---

## Estimado de Recursos

| Componente | RAM | CPU |
|------------|-----|-----|
| iqbot-core (Python + APScheduler) | ~200MB | <5% |
| iqbot-dashboard (Nginx sirviendo React) | ~50MB | <1% |
| PostgreSQL | ~200MB | <3% |
| Redis | ~50MB | <1% |
| **Total** | **~500MB** | **<10%** |

Un servidor con 1GB RAM y 1 vCPU es suficiente.

---

## Convenciones de Código

### Commits (Conventional Commits en español)
```
feat(bot): agregar detección de patrón BB squeeze
fix(gpt): corregir parsing de respuesta JSON
chore(docker): configurar docker-compose con postgres y redis
db(migraciones): crear tabla operaciones con columna indicadores_snapshot
style(dashboard): ajustar colores del panel de logs
```

### Nombres
- Archivos Python: snake_case → `bot_engine.py`
- Archivos React: PascalCase → `LogsPanel.jsx`
- Variables Python: snake_case → `umbral_confianza`
- Variables JS: camelCase → `umbralConfianza`
- Constantes: UPPER_SNAKE_CASE → `MAX_OPS_POR_HORA`

### Estructura de ramas
```
main       → producción, solo merge con PR
develop    → integración
feature/   → nueva funcionalidad
fix/       → corrección de bug
chore/     → configuración y setup
```

---

## Orden de Implementación para Claude Code

Implementar en este orden exacto, sin saltarse pasos:

1. **Setup base** — docker-compose.yml, Dockerfiles, .env.example, estructura de carpetas
2. **Modelos BD + migraciones** — crear tablas, correr Alembic
3. **Auth** — login con JWT, crear usuario admin desde .env al startup
4. **iqoption_service.py** — conexión, obtener velas, ejecutar operación
5. **indicator_service.py** — RSI, EMA, Bollinger con pandas-ta
6. **pattern_service.py** — los 3 patrones
7. **ml_service.py** — XGBoost con data inicial de yfinance + función de reentrenamiento
8. **gpt_service.py** — llamada a GPT-4o mini con el prompt definido
9. **human_behavior.py** — delays y anti-detección
10. **bot_engine.py** — loop principal con APScheduler integrando todo lo anterior
11. **Routers FastAPI** — auth, bot, config, operaciones, WebSocket logs
12. **Dashboard React** — en el orden: Login → BotControls → Stats → Config → Tabla → Logs

---

## Lo que Claude Code debe recordar siempre

- Leer este documento completo antes de escribir código
- El bot NUNCA hardcodea credenciales — todo viene del .env
- Los delays aleatorios son obligatorios antes de cada operación (anti-detección)
- La configuración se lee desde Redis (cache) no desde PostgreSQL en cada ciclo
- Los cambios de configuración desde el dashboard se escriben en PostgreSQL Y Redis simultáneamente
- El WebSocket de logs debe reconectarse automáticamente en el frontend
- Antes de cambiar a modo REAL desde el dashboard, mostrar modal de confirmación
- El modelo XGBoost se guarda en `iqbot-core/model.pkl` y se carga al iniciar
- Si `model.pkl` no existe al iniciar, generar uno con data histórica de yfinance automáticamente
- Nunca instalar librerías no listadas en este documento sin preguntar

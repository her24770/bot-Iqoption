"""Aplicación FastAPI: routers, CORS, WebSocket y arranque del bot."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models.configuracion import Configuracion
from app.models.usuario import Usuario
from app.routers import auth, bot, config, operaciones, ws
from app.routers.auth import hash_password
from app.services.bot_engine import bot_engine
from app.services.config_cache import sync_config_a_redis
from app.utils.logger import log_event


def _crear_tablas() -> None:
    """Red de seguridad: si las migraciones Alembic no corrieron, crea las tablas."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        log_event("ERROR", f"No se pudieron crear tablas: {exc}")


def _aplicar_migraciones() -> None:
    """Agrega columnas nuevas a tablas existentes sin romper instalaciones anteriores."""
    migraciones = [
        "ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS intervalo_ciclo_minutos INTEGER DEFAULT 5",
    ]
    try:
        with engine.connect() as conn:
            for sql in migraciones:
                conn.execute(text(sql))
            conn.commit()
    except Exception as exc:
        log_event("WARNING", f"Migración omitida (puede ser normal en BD nueva): {exc}")


def _seed() -> None:
    """Crea el usuario admin y la fila de configuración (id=1) si no existen."""
    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == settings.DASHBOARD_EMAIL).first()
        if not admin:
            admin = Usuario(
                email=settings.DASHBOARD_EMAIL,
                password_hash=hash_password(settings.DASHBOARD_PASSWORD),
            )
            db.add(admin)
            log_event("INFO", f"Usuario admin creado: {settings.DASHBOARD_EMAIL}")

        config = db.query(Configuracion).get(1)
        if not config:
            config = Configuracion(id=1)
            db.add(config)
            log_event("INFO", "Configuración inicial creada")
        db.commit()
        db.refresh(config)
        sync_config_a_redis(config)
    except Exception as exc:
        log_event("ERROR", f"Error en seed inicial: {exc}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _crear_tablas()
    _aplicar_migraciones()
    _seed()
    bot_engine.iniciar()
    log_event("SUCCESS", "IQBot Core iniciado correctamente")
    yield
    bot_engine.detener_scheduler()


app = FastAPI(title="IQBot Core", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bot.router)
app.include_router(config.router)
app.include_router(operaciones.router)
app.include_router(ws.router)


@app.get("/")
def root():
    return {"app": "IQBot Core", "status": "ok", "simulacion": bot_engine.iq.simulation}


@app.get("/health")
def health():
    return {"status": "ok"}

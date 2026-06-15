"""Configuración en vivo del bot (sin reiniciar)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.configuracion import Configuracion
from app.routers.auth import get_current_user
from app.schemas.configuracion import ConfiguracionOut, ConfiguracionUpdate
from app.services.bot_engine import bot_engine
from app.services.config_cache import sync_config_a_redis
from app.utils.logger import log_event
from app.utils.responses import api_error

router = APIRouter(prefix="/config", tags=["config"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=ConfiguracionOut)
def obtener_config(db: Session = Depends(get_db)):
    config = db.query(Configuracion).get(1)
    if not config:
        raise api_error("CONFIG_NO_ENCONTRADA", "No existe configuración", 404)
    return config


@router.put("", response_model=ConfiguracionOut)
def actualizar_config(datos: ConfiguracionUpdate, db: Session = Depends(get_db)):
    config = db.query(Configuracion).get(1)
    if not config:
        raise api_error("CONFIG_NO_ENCONTRADA", "No existe configuración", 404)

    cambios = datos.model_dump(exclude_unset=True)

    if "modo" in cambios and cambios["modo"] not in ("demo", "real"):
        raise api_error("MODO_INVALIDO", "El modo debe ser 'demo' o 'real'", 422)

    modo_anterior = config.modo
    for campo, valor in cambios.items():
        setattr(config, campo, valor)
    db.commit()
    db.refresh(config)

    # Se escribe en PostgreSQL Y Redis simultáneamente
    sync_config_a_redis(config)

    if "modo" in cambios and cambios["modo"] != modo_anterior:
        bot_engine.iq.cambiar_modo(config.modo)
        log_event("WARNING", f"Modo cambiado a {config.modo.upper()}")

    if "intervalo_ciclo_minutos" in cambios:
        bot_engine.reagendar_ciclo(config.intervalo_ciclo_minutos)

    log_event("INFO", f"Configuración actualizada: {', '.join(cambios.keys())}")
    return config

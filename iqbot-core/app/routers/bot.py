"""Control del bot: start, stop, status."""
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.configuracion import Configuracion
from app.redis_client import redis_client
from app.routers.auth import get_current_user
from app.services.bot_engine import ESTADO_KEY, RATE_KEY, bot_engine
from app.services.config_cache import sync_config_a_redis
from app.utils.logger import log_event

router = APIRouter(prefix="/bot", tags=["bot"], dependencies=[Depends(get_current_user)])


def _get_config(db: Session) -> Configuracion:
    return db.query(Configuracion).get(1)


@router.post("/start")
def start(db: Session = Depends(get_db)):
    config = _get_config(db)
    config.activo = True
    db.commit()
    sync_config_a_redis(config)
    bot_engine.iq.cambiar_modo(config.modo)
    bot_engine._actualizar_estado(estado="activo", activo=True, par=config.par, modo=config.modo)
    log_event("SUCCESS", "Bot activado")
    return {"activo": True, "mensaje": "Bot activado"}


@router.post("/stop")
def stop(db: Session = Depends(get_db)):
    config = _get_config(db)
    config.activo = False
    db.commit()
    sync_config_a_redis(config)
    bot_engine._actualizar_estado(estado="detenido", activo=False)
    log_event("WARNING", "Bot detenido manualmente")
    return {"activo": False, "mensaje": "Bot detenido"}


@router.get("/status")
def status(db: Session = Depends(get_db)):
    config = _get_config(db)
    try:
        raw = redis_client.get(ESTADO_KEY)
        estado = json.loads(raw) if raw else {}
    except Exception:
        estado = {}
    ops_hora = int(redis_client.get(RATE_KEY) or 0)
    balance = bot_engine.iq.obtener_balance(config.modo)
    return {
        "activo": config.activo,
        "estado": estado.get("estado", "detenido" if not config.activo else "activo"),
        "par": config.par,
        "modo": config.modo,
        "simulacion": bot_engine.iq.simulation,
        "balance": balance,
        "ops_esta_hora": ops_hora,
        "max_ops_por_hora": config.max_ops_por_hora,
        "ultima_operacion": estado.get("ultima_operacion"),
    }

"""Control del bot: start, stop, status."""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.configuracion import Configuracion
from app.models.operacion import Operacion
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


class OperarManualIn(BaseModel):
    direccion: str          # "CALL" o "PUT"
    par: Optional[str] = None
    monto: Optional[float] = None


@router.post("/operar-manual")
def operar_manual(datos: OperarManualIn, db: Session = Depends(get_db)):
    direccion = datos.direccion.upper()
    if direccion not in ("CALL", "PUT"):
        return {"ok": False, "mensaje": "Dirección debe ser CALL o PUT"}

    config = _get_config(db)
    par = datos.par or config.par

    if bot_engine.iq.simulation and not bot_engine.iq.modo_simulacion_forzado:
        return {"ok": False, "mensaje": "Sin conexión real a IQ Option"}

    if not bot_engine.iq.activo_disponible(par):
        return {"ok": False, "mensaje": f"Mercado cerrado para {par} en este momento"}

    balance = bot_engine.iq.obtener_balance(config.modo)
    monto = datos.monto or round(balance * config.monto_porcentaje_balance, 2)

    order_id = bot_engine.iq.ejecutar(par, direccion, monto, config.modo, duracion=5)
    if order_id is None and not bot_engine.iq.simulation:
        return {"ok": False, "mensaje": "IQ Option rechazó la operación"}

    ahora = datetime.utcnow()
    op = Operacion(
        id=uuid.uuid4(),
        par=par,
        direccion=direccion,
        monto=monto,
        resultado="PENDING",
        ganancia=0.0,
        patron_activado="Manual",
        confianza_ml=1.0,
        decision_gpt=direccion,
        modo=config.modo,
        indicadores_snapshot={"origen": "manual"},
        created_at=ahora,
        expires_at=ahora + timedelta(minutes=5),
    )
    db.add(op)
    db.commit()
    db.refresh(op)

    bot_engine.scheduler.add_job(
        bot_engine.resolver,
        "date",
        run_date=op.expires_at,
        args=[str(op.id), order_id],
        id=f"resolver_{op.id}",
        replace_existing=True,
    )

    log_event("SUCCESS", f"Operación MANUAL: {direccion} ${monto} en {par}")
    return {"ok": True, "mensaje": f"{direccion} ${monto} en {par} ejecutada", "op_id": str(op.id)}


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

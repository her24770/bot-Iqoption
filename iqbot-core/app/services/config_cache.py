"""Sincronización de la configuración entre PostgreSQL y Redis.

Regla del proyecto: el bot lee la config desde Redis (rápido). Cada cambio
desde el dashboard se escribe en PostgreSQL Y Redis simultáneamente.
"""
import json
from typing import Optional

from app.models.configuracion import Configuracion
from app.redis_client import redis_client

CONFIG_KEY = "bot:config"

CAMPOS = [
    "par",
    "modo",
    "activo",
    "umbral_confianza",
    "max_ops_por_hora",
    "monto_porcentaje_balance",
    "perdidas_consecutivas_limite",
    "reentrenar_cada_n_ops",
    "intervalo_ciclo_minutos",
]


def config_a_dict(config: Configuracion) -> dict:
    return {campo: getattr(config, campo) for campo in CAMPOS}


def sync_config_a_redis(config: Configuracion) -> None:
    try:
        redis_client.set(CONFIG_KEY, json.dumps(config_a_dict(config)))
    except Exception:
        pass


def get_config_cache() -> Optional[dict]:
    """Lee la config desde Redis. Devuelve None si no está cacheada."""
    try:
        raw = redis_client.get(CONFIG_KEY)
        return json.loads(raw) if raw else None
    except Exception:
        return None

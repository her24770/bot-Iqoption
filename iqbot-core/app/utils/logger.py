"""Logger con persistencia en Redis y broadcast a clientes WebSocket.

Niveles soportados: INFO, WARNING, ERROR, SUCCESS.
- INFO/WARNING/ERROR se mapean a logging estándar.
- SUCCESS es un nivel propio para el dashboard (verde).
Los últimos 200 logs se guardan en Redis (logs:stream) para reconexión.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List

from app.redis_client import redis_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
_logger = logging.getLogger("iqbot")

LOGS_KEY = "logs:stream"
MAX_LOGS = 200


class WSManager:
    """Gestiona las conexiones WebSocket activas para el stream de logs."""

    def __init__(self) -> None:
        self.connections: List = []

    async def connect(self, websocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        muertas = []
        for ws in list(self.connections):
            try:
                await ws.send_json(message)
            except Exception:
                muertas.append(ws)
        for ws in muertas:
            self.disconnect(ws)


ws_manager = WSManager()


def _persistir(entry: dict) -> None:
    try:
        redis_client.lpush(LOGS_KEY, json.dumps(entry))
        redis_client.ltrim(LOGS_KEY, 0, MAX_LOGS - 1)
    except Exception:
        pass


def _broadcast(entry: dict) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast(entry))
    except RuntimeError:
        # No hay event loop corriendo (contexto síncrono): solo se persiste.
        pass


def obtener_logs_recientes() -> List[dict]:
    """Devuelve los logs guardados en Redis (más recientes primero invertidos a cronológico)."""
    try:
        raw = redis_client.lrange(LOGS_KEY, 0, MAX_LOGS - 1)
        return [json.loads(x) for x in reversed(raw)]
    except Exception:
        return []


def log_event(level: str, message: str) -> dict:
    """Registra un evento: consola + Redis + broadcast WebSocket."""
    level = level.upper()
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
    }
    py_level = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "SUCCESS": logging.INFO,
    }.get(level, logging.INFO)
    _logger.log(py_level, message)
    _persistir(entry)
    _broadcast(entry)
    return entry

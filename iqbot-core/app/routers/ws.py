"""WebSocket de logs en tiempo real. Autenticado con JWT en query param."""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.routers.auth import decodificar_token
from app.utils.logger import obtener_logs_recientes, ws_manager

router = APIRouter()


@router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket, token: str = Query(None)):
    # Autenticación por token en query param
    if not token or not decodificar_token(token):
        await websocket.close(code=1008)
        return

    await ws_manager.connect(websocket)
    try:
        # Enviar el histórico reciente al conectar (para reconexión)
        for entry in obtener_logs_recientes():
            await websocket.send_json(entry)
        # Mantener la conexión viva
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

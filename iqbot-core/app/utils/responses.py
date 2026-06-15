"""Respuestas de error estándar de la API."""
from fastapi import HTTPException


def api_error(code: str, message: str, status_code: int = 400) -> HTTPException:
    """Genera una HTTPException con el formato estándar del proyecto.

    El detail sigue la forma: {"error": true, "code": ..., "message": ...}
    """
    return HTTPException(
        status_code=status_code,
        detail={"error": True, "code": code, "message": message},
    )

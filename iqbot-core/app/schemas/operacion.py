from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class OperacionOut(BaseModel):
    id: str
    par: str
    direccion: str
    monto: float
    resultado: str
    ganancia: float
    patron_activado: Optional[str] = None
    confianza_ml: Optional[float] = None
    decision_gpt: Optional[str] = None
    modo: str
    created_at: datetime


class OperacionesPagina(BaseModel):
    total: int
    page: int
    limit: int
    items: List[OperacionOut]


class PatronStat(BaseModel):
    patron: str
    total: int
    wins: int
    win_rate: float


class PuntoRendimiento(BaseModel):
    fecha: str
    pnl_acumulado: float


class StatsResponse(BaseModel):
    total_operaciones: int
    wins: int
    loses: int
    win_rate: float
    pnl_total: float
    por_patron: List[PatronStat]
    rendimiento: List[PuntoRendimiento]

from typing import Optional

from pydantic import BaseModel


class ConfiguracionOut(BaseModel):
    par: str
    modo: str
    activo: bool
    umbral_confianza: float
    max_ops_por_hora: int
    monto_porcentaje_balance: float
    perdidas_consecutivas_limite: int
    reentrenar_cada_n_ops: int
    intervalo_ciclo_minutos: int

    class Config:
        from_attributes = True


class ConfiguracionUpdate(BaseModel):
    par: Optional[str] = None
    modo: Optional[str] = None
    umbral_confianza: Optional[float] = None
    max_ops_por_hora: Optional[int] = None
    monto_porcentaje_balance: Optional[float] = None
    perdidas_consecutivas_limite: Optional[int] = None
    reentrenar_cada_n_ops: Optional[int] = None
    intervalo_ciclo_minutos: Optional[int] = None

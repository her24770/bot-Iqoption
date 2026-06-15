"""Modelo de configuración persistente del bot (siempre una sola fila, id=1)."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime

from app.database import Base


class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True, default=1)
    par = Column(String, default="EURUSD")
    modo = Column(String, default="demo")                       # demo | real
    activo = Column(Boolean, default=False)
    umbral_confianza = Column(Float, default=0.70)
    max_ops_por_hora = Column(Integer, default=6)
    monto_porcentaje_balance = Column(Float, default=0.02)      # 2% del balance
    perdidas_consecutivas_limite = Column(Integer, default=3)
    reentrenar_cada_n_ops = Column(Integer, default=100)
    intervalo_ciclo_minutos = Column(Integer, default=5)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

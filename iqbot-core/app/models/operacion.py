"""Modelo del historial de operaciones."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Operacion(Base):
    __tablename__ = "operaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    par = Column(String, nullable=False)
    direccion = Column(String, nullable=False)          # CALL | PUT
    monto = Column(Float, nullable=False)
    resultado = Column(String, default="PENDING")       # WIN | LOSE | PENDING
    ganancia = Column(Float, default=0.0)
    patron_activado = Column(String)
    confianza_ml = Column(Float)
    decision_gpt = Column(String)                        # CALL | PUT | SKIP
    modo = Column(String, nullable=False)                # demo | real
    indicadores_snapshot = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

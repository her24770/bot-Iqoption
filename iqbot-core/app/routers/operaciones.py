"""Historial de operaciones, métricas y exportación CSV."""
import csv
import io
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.operacion import Operacion
from app.routers.auth import get_current_user
from app.schemas.operacion import (
    OperacionesPagina,
    OperacionOut,
    PatronStat,
    PuntoRendimiento,
    StatsResponse,
)

router = APIRouter(prefix="/operaciones", tags=["operaciones"], dependencies=[Depends(get_current_user)])


def _to_out(op: Operacion) -> OperacionOut:
    return OperacionOut(
        id=str(op.id),
        par=op.par,
        direccion=op.direccion,
        monto=op.monto,
        resultado=op.resultado,
        ganancia=op.ganancia or 0.0,
        patron_activado=op.patron_activado,
        confianza_ml=op.confianza_ml,
        decision_gpt=op.decision_gpt,
        modo=op.modo,
        created_at=op.created_at,
    )


@router.get("", response_model=OperacionesPagina)
def listar(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    modo: Optional[str] = Query(None, pattern="^(demo|real)$"),
    db: Session = Depends(get_db),
):
    q = db.query(Operacion)
    if modo:
        q = q.filter(Operacion.modo == modo)
    total = q.count()
    items = (
        q.order_by(Operacion.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return OperacionesPagina(
        total=total,
        page=page,
        limit=limit,
        items=[_to_out(o) for o in items],
    )


@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)):
    cerradas = (
        db.query(Operacion).filter(Operacion.resultado.in_(["WIN", "LOSE"])).all()
    )
    total = len(cerradas)
    wins = sum(1 for o in cerradas if o.resultado == "WIN")
    loses = total - wins
    win_rate = round(wins / total * 100, 1) if total else 0.0
    pnl_total = round(sum(o.ganancia or 0.0 for o in cerradas), 2)

    # Win rate por patrón
    por_patron_map = defaultdict(lambda: {"total": 0, "wins": 0})
    for o in cerradas:
        nombre = o.patron_activado or "Desconocido"
        por_patron_map[nombre]["total"] += 1
        if o.resultado == "WIN":
            por_patron_map[nombre]["wins"] += 1
    por_patron = [
        PatronStat(
            patron=nombre,
            total=d["total"],
            wins=d["wins"],
            win_rate=round(d["wins"] / d["total"] * 100, 1) if d["total"] else 0.0,
        )
        for nombre, d in por_patron_map.items()
    ]

    # Rendimiento acumulado por día
    por_dia = defaultdict(float)
    for o in sorted(cerradas, key=lambda x: x.created_at):
        fecha = o.created_at.strftime("%Y-%m-%d")
        por_dia[fecha] += o.ganancia or 0.0
    acumulado = 0.0
    rendimiento = []
    for fecha in sorted(por_dia.keys()):
        acumulado += por_dia[fecha]
        rendimiento.append(PuntoRendimiento(fecha=fecha, pnl_acumulado=round(acumulado, 2)))

    return StatsResponse(
        total_operaciones=total,
        wins=wins,
        loses=loses,
        win_rate=win_rate,
        pnl_total=pnl_total,
        por_patron=por_patron,
        rendimiento=rendimiento,
    )


@router.get("/export/csv")
def exportar_csv(db: Session = Depends(get_db)):
    operaciones = db.query(Operacion).order_by(Operacion.created_at.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "fecha", "par", "direccion", "monto", "resultado", "ganancia",
        "patron", "confianza_ml", "decision_gpt", "modo",
    ])
    for o in operaciones:
        writer.writerow([
            o.created_at.isoformat(),
            o.par,
            o.direccion,
            o.monto,
            o.resultado,
            o.ganancia,
            o.patron_activado,
            o.confianza_ml,
            o.decision_gpt,
            o.modo,
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=operaciones.csv"},
    )

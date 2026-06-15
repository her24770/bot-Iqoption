"""Detección de los 3 patrones de trading definidos en la planificación."""
from typing import List

import pandas as pd

# Mapeo patrón -> id numérico para el modelo XGBoost
PATRON_IDS = {
    "RSI Reversal": 1,
    "EMA Cross": 2,
    "BB Squeeze": 3,
}


def detectar_patrones(df: pd.DataFrame) -> List[dict]:
    """Devuelve la lista de patrones activos en la última vela.

    Cada patrón: {"id": int, "nombre": str, "direccion": "CALL"|"PUT"}.
    """
    if len(df) < 2:
        return []

    last = df.iloc[-1]
    prev = df.iloc[-2]
    patrones: List[dict] = []

    # --- Patrón 1: RSI Reversal + vela envolvente ---
    if last["rsi"] < 30 and last["close"] > prev["close"]:
        patrones.append({"id": 1, "nombre": "RSI Reversal", "direccion": "CALL"})
    elif last["rsi"] > 70 and last["close"] < prev["close"]:
        patrones.append({"id": 1, "nombre": "RSI Reversal", "direccion": "PUT"})

    # --- Patrón 2: Cruce de EMAs con volumen ---
    cruce_arriba = prev["ema9"] <= prev["ema21"] and last["ema9"] > last["ema21"]
    cruce_abajo = prev["ema9"] >= prev["ema21"] and last["ema9"] < last["ema21"]
    volumen_alto = last["volume"] > (last["vol_avg20"] or 0) * 1.2
    if cruce_arriba and volumen_alto:
        patrones.append({"id": 2, "nombre": "EMA Cross", "direccion": "CALL"})
    elif cruce_abajo and volumen_alto:
        patrones.append({"id": 2, "nombre": "EMA Cross", "direccion": "PUT"})

    # --- Patrón 3: Bollinger Squeeze ---
    if last["close"] <= last["bb_lower"] and 30 <= last["rsi"] <= 50:
        patrones.append({"id": 3, "nombre": "BB Squeeze", "direccion": "CALL"})
    elif last["close"] >= last["bb_upper"] and 50 <= last["rsi"] <= 70:
        patrones.append({"id": 3, "nombre": "BB Squeeze", "direccion": "PUT"})

    return patrones

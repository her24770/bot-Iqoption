"""Cálculo de indicadores técnicos: RSI, EMA, Bollinger Bands y volumen.

Implementado con pandas/numpy puro (sin pandas-ta, que dejó de ser instalable
en Python 3.11). Las fórmulas son las estándar del análisis técnico.
"""
import numpy as np
import pandas as pd


def _rsi(close: pd.Series, length: int = 14) -> pd.Series:
    """RSI de Wilder."""
    delta = close.diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    avg_ganancia = ganancia.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_perdida = perdida.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_ganancia / avg_perdida.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _ema(close: pd.Series, length: int) -> pd.Series:
    return close.ewm(span=length, adjust=False).mean()


def calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe un DataFrame con columnas open, high, low, close, volume.

    Devuelve el mismo DataFrame con columnas de indicadores añadidas.
    """
    df = df.copy()

    df["rsi"] = _rsi(df["close"], 14)
    df["ema9"] = _ema(df["close"], 9)
    df["ema21"] = _ema(df["close"], 21)

    # Bollinger Bands (20, 2)
    media = df["close"].rolling(20).mean()
    std = df["close"].rolling(20).std()
    df["bb_mid"] = media.fillna(df["close"])
    df["bb_upper"] = (media + 2 * std).fillna(df["close"])
    df["bb_lower"] = (media - 2 * std).fillna(df["close"])

    df["vol_avg20"] = df["volume"].rolling(20).mean()

    return df


def snapshot_indicadores(df: pd.DataFrame) -> dict:
    """Devuelve un snapshot (dict) de los indicadores en la última vela."""
    last = df.iloc[-1]
    bb_rango = float(last["bb_upper"] - last["bb_lower"]) or 1e-9
    vol_avg = float(last["vol_avg20"]) if pd.notna(last["vol_avg20"]) else float(last["volume"]) or 1e-9

    return {
        "rsi": _num(last["rsi"]),
        "ema9": _num(last["ema9"]),
        "ema21": _num(last["ema21"]),
        "ema_diff": _num(last["ema9"]) - _num(last["ema21"]),
        "bb_lower": _num(last["bb_lower"]),
        "bb_mid": _num(last["bb_mid"]),
        "bb_upper": _num(last["bb_upper"]),
        "bb_position": (float(last["close"]) - float(last["bb_lower"])) / bb_rango,
        "precio": float(last["close"]),
        "volumen": float(last["volume"]),
        "vol_avg20": vol_avg,
        "vol_ratio": float(last["volume"]) / vol_avg,
    }


def _num(valor) -> float:
    try:
        if pd.isna(valor):
            return 0.0
        return float(valor)
    except Exception:
        return 0.0

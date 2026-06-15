"""Servicio de Machine Learning: scoring de señales y reentrenamiento con XGBoost.

El modelo se guarda en disco (settings.MODEL_PATH). Si no existe al iniciar,
se entrena uno inicial con data histórica de yfinance (EUR/USD). Si yfinance
falla (sin red), se usa un dataset sintético para que el modelo siempre exista.
"""
import os
import pickle
from typing import List, Optional

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from app.config import settings
from app.services.indicator_service import calcular_indicadores
from app.utils.logger import log_event

# Orden de features esperado por el modelo
FEATURES = ["rsi", "ema_diff", "bb_position", "vol_ratio", "patron_id", "hora_del_dia"]


class MLService:
    def __init__(self) -> None:
        self.model: Optional[XGBClassifier] = None

    # ------------------------------------------------------------------ carga
    def cargar_o_entrenar(self) -> None:
        if os.path.exists(settings.MODEL_PATH):
            try:
                with open(settings.MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                log_event("INFO", "Modelo XGBoost cargado desde disco")
                return
            except Exception as exc:
                log_event("ERROR", f"No se pudo cargar model.pkl: {exc}. Reentrenando...")
        self.entrenar_inicial()

    def _guardar(self) -> None:
        try:
            with open(settings.MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
        except Exception as exc:
            log_event("ERROR", f"No se pudo guardar el modelo: {exc}")

    # ------------------------------------------------- entrenamiento inicial
    def entrenar_inicial(self) -> None:
        X, y = self._datos_historicos()
        self.model = self._nuevo_modelo()
        self.model.fit(X, y)
        self._guardar()
        log_event("SUCCESS", f"Modelo inicial entrenado con {len(y)} muestras")

    def _nuevo_modelo(self) -> XGBClassifier:
        return XGBClassifier(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.9,
            eval_metric="logloss",
            use_label_encoder=False,
        )

    def _datos_historicos(self):
        """Genera (X, y) para el entrenamiento inicial desde yfinance o sintético."""
        try:
            import yfinance as yf

            data = yf.download(
                "EURUSD=X", period="60d", interval="5m", progress=False
            )
            if data is None or data.empty:
                raise ValueError("yfinance devolvió data vacía")

            df = pd.DataFrame({
                "open": data["Open"].squeeze(),
                "high": data["High"].squeeze(),
                "low": data["Low"].squeeze(),
                "close": data["Close"].squeeze(),
                "volume": data["Volume"].squeeze().fillna(1000),
            }).reset_index(drop=True)

            df = calcular_indicadores(df)
            df["ema_diff"] = df["ema9"] - df["ema21"]
            rango = (df["bb_upper"] - df["bb_lower"]).replace(0, 1e-9)
            df["bb_position"] = (df["close"] - df["bb_lower"]) / rango
            df["vol_ratio"] = df["volume"] / df["vol_avg20"].replace(0, 1e-9)
            df["patron_id"] = 0
            df["hora_del_dia"] = pd.to_datetime(data.index).hour[: len(df)]
            # Label: la siguiente vela cierra por encima de la actual (1) o no (0)
            df["label"] = (df["close"].shift(-1) > df["close"]).astype(int)
            df = df.dropna()

            X = df[FEATURES].astype(float).values
            y = df["label"].astype(int).values
            if len(y) < 50:
                raise ValueError("Pocas muestras tras limpieza")
            log_event("INFO", f"Data histórica de yfinance cargada: {len(y)} velas")
            return X, y
        except Exception as exc:
            log_event(
                "WARNING",
                f"yfinance no disponible ({exc}). Usando dataset sintético inicial.",
            )
            return self._datos_sinteticos()

    def _datos_sinteticos(self, n: int = 800):
        """Dataset sintético con algo de señal para arrancar el modelo."""
        rng = np.random.default_rng(42)
        rsi = rng.uniform(10, 90, n)
        ema_diff = rng.normal(0, 0.001, n)
        bb_position = rng.uniform(0, 1, n)
        vol_ratio = rng.uniform(0.5, 2.5, n)
        patron_id = rng.integers(0, 4, n)
        hora = rng.integers(0, 24, n)

        # Señal artificial: RSI extremo + buena posición BB => más probable WIN
        score = (
            (rsi < 30).astype(float) * 0.4
            + (rsi > 70).astype(float) * 0.4
            + (bb_position < 0.2).astype(float) * 0.3
            + (vol_ratio > 1.2).astype(float) * 0.2
            + rng.normal(0, 0.3, n)
        )
        y = (score > 0.4).astype(int)
        X = np.column_stack([rsi, ema_diff, bb_position, vol_ratio, patron_id, hora])
        return X, y

    # ------------------------------------------------------------- inferencia
    def score(self, features: dict) -> float:
        """Devuelve la probabilidad (0–1) de que la señal sea ganadora."""
        if self.model is None:
            self.cargar_o_entrenar()
        x = np.array([[float(features.get(f, 0.0)) for f in FEATURES]])
        try:
            proba = self.model.predict_proba(x)[0][1]
            return float(proba)
        except Exception as exc:
            log_event("ERROR", f"Error en scoring ML: {exc}")
            return 0.0

    # --------------------------------------------------------- reentrenamiento
    def reentrenar(self, operaciones: List[dict]) -> Optional[float]:
        """Reentrena el modelo con operaciones reales (resultado WIN/LOSE).

        operaciones: lista de dicts con 'snapshot' (indicadores), 'patron_id',
        'hora', 'label' (1=WIN, 0=LOSE).
        Devuelve el accuracy aproximado, o None si no hay datos suficientes.
        """
        filas = []
        labels = []
        for op in operaciones:
            snap = op.get("snapshot") or {}
            filas.append([
                float(snap.get("rsi", 0.0)),
                float(snap.get("ema_diff", 0.0)),
                float(snap.get("bb_position", 0.0)),
                float(snap.get("vol_ratio", 0.0)),
                float(op.get("patron_id", 0)),
                float(op.get("hora", 0)),
            ])
            labels.append(int(op["label"]))

        if len(set(labels)) < 2 or len(labels) < 20:
            log_event("WARNING", "Datos insuficientes para reentrenar (se mantiene el modelo)")
            return None

        X = np.array(filas)
        y = np.array(labels)

        try:
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score

            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=7)
            modelo = self._nuevo_modelo()
            modelo.fit(X_tr, y_tr)
            acc = accuracy_score(y_te, modelo.predict(X_te))
            self.model = modelo
            self._guardar()
            log_event("SUCCESS", f"Modelo reentrenado con {len(y)} operaciones. Accuracy: {acc:.0%}")
            return float(acc)
        except Exception as exc:
            log_event("ERROR", f"Error en reentrenamiento: {exc}")
            return None

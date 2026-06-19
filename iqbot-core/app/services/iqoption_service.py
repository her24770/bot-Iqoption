"""Conexión y ejecución de operaciones en IQ Option.

Modo SIMULACIÓN automático: si la librería iqoptionapi no está disponible o no
hay credenciales válidas, el servicio genera velas, balance y resultados
sintéticos para que todo el stack funcione localmente sin una cuenta real.
En el servidor, con credenciales reales, se conecta a IQ Option de verdad.
"""
import concurrent.futures
import random
import time
from typing import Optional

import numpy as np
import pandas as pd

from app.config import settings
from app.utils.logger import log_event

try:
    from iqoptionapi.stable_api import IQ_Option  # type: ignore

    IQOPTION_DISPONIBLE = True
except Exception:
    IQOPTION_DISPONIBLE = False

PAYOUT = 0.85  # ganancia sobre el monto en caso de WIN


class IQOptionService:
    def __init__(self) -> None:
        self.api = None
        self.simulation = True
        self._precio_sim = 1.10000

    # ------------------------------------------------------------- propiedades
    @property
    def modo_simulacion_forzado(self) -> bool:
        """True solo cuando NO hay credenciales o la librería no está disponible."""
        return (
            not IQOPTION_DISPONIBLE
            or not settings.IQOPTION_EMAIL
            or not settings.IQOPTION_PASSWORD
        )

    # ------------------------------------------------------------- conexión
    def conectar(self) -> bool:
        if self.modo_simulacion_forzado:
            self.simulation = True
            log_event(
                "WARNING",
                "IQ Option en modo SIMULACIÓN (librería no disponible o sin credenciales)",
            )
            return False
        return self._intentar_conexion()

    def _intentar_conexion(self) -> bool:
        """Conecta o reconecta a IQ Option. Retorna True si éxito."""
        try:
            self.api = IQ_Option(settings.IQOPTION_EMAIL, settings.IQOPTION_PASSWORD)
            ok, reason = self.api.connect()
            if ok:
                self.simulation = False
                log_event("SUCCESS", "Conectado a IQ Option (cuenta PRACTICE)")
                self.cambiar_modo("demo")
                return True
            log_event("ERROR", f"No se pudo conectar a IQ Option: {reason}")
        except Exception as exc:
            log_event("ERROR", f"Error conectando a IQ Option: {exc}")
        self.simulation = True
        return False

    def reconectar(self) -> bool:
        """Reconexión explícita cuando la sesión expira. Retorna True si éxito."""
        if self.modo_simulacion_forzado:
            return False
        log_event("WARNING", "Sesión de IQ Option expirada. Reconectando...")
        return self._intentar_conexion()

    def cambiar_modo(self, modo: str) -> None:
        if not self.simulation and self.api:
            try:
                self.api.change_balance("PRACTICE" if modo == "demo" else "REAL")
            except Exception as exc:
                log_event("ERROR", f"No se pudo cambiar el modo de balance: {exc}")

    # -------------------------------------------------------------- balance
    def obtener_balance(self, modo: str) -> float:
        if not self.simulation and self.api:
            try:
                return float(self.api.get_balance())
            except Exception as exc:
                log_event("ERROR", f"No se pudo obtener balance real: {exc}")
        return 10000.0 if modo == "demo" else 500.0

    # ---------------------------------------------------------------- velas
    def obtener_velas(self, par: str, cantidad: int = 50, timeframe: int = 300) -> pd.DataFrame:
        if not self.simulation and self.api:
            try:
                fin = time.time()
                velas = self.api.get_candles(par, timeframe, cantidad, fin)
                df = pd.DataFrame(velas)
                df = df.rename(columns={"min": "low", "max": "high"})
                return df[["open", "high", "low", "close", "volume"]].astype(float)
            except Exception as exc:
                log_event("ERROR", f"Error obteniendo velas: {exc}. Intentando reconectar...")
                if self.reconectar():
                    try:
                        fin = time.time()
                        velas = self.api.get_candles(par, timeframe, cantidad, fin)
                        df = pd.DataFrame(velas)
                        df = df.rename(columns={"min": "low", "max": "high"})
                        return df[["open", "high", "low", "close", "volume"]].astype(float)
                    except Exception as exc2:
                        log_event("ERROR", f"Error post-reconexión obteniendo velas: {exc2}")
                        self.simulation = True

        if self.simulation and not self.modo_simulacion_forzado:
            log_event("WARNING", "⚠️  SIMULACIÓN ACTIVA — sin conexión real a IQ Option")
        return self._velas_simuladas(cantidad)

    def _velas_simuladas(self, cantidad: int) -> pd.DataFrame:
        """Genera velas con un random walk para que los indicadores funcionen."""
        rng = np.random.default_rng()
        precio = self._precio_sim
        filas = []
        for _ in range(cantidad):
            cambio = rng.normal(0, 0.0006)
            open_ = precio
            close = max(0.5, precio + cambio)
            high = max(open_, close) + abs(rng.normal(0, 0.0003))
            low = min(open_, close) - abs(rng.normal(0, 0.0003))
            volume = abs(rng.normal(1000, 350))
            filas.append([open_, high, low, close, volume])
            precio = close
        self._precio_sim = precio
        return pd.DataFrame(filas, columns=["open", "high", "low", "close", "volume"])

    # ------------------------------------------------------------- ejecución
    def activo_disponible(self, par: str) -> bool:
        """Verifica si el activo está abierto para opciones digitales."""
        if self.simulation or not self.api:
            return True
        try:
            tiempos = self.api.get_all_open_time()
            digital = tiempos.get("digital", {}).get(par, {})
            turbo = tiempos.get("turbo", {}).get(par, {})
            binaria = tiempos.get("binary", {}).get(par, {})
            return (
                digital.get("open", False)
                or turbo.get("open", False)
                or binaria.get("open", False)
            )
        except Exception:
            return True  # ante la duda, intentar

    def ejecutar(self, par: str, direccion: str, monto: float, modo: str, duracion: int = 5):
        """Ejecuta la operación con opciones digitales (mayor disponibilidad horaria).
        Devuelve un identificador de orden (o None si falla/simulación).
        """
        if self.simulation:
            if not self.modo_simulacion_forzado:
                log_event("WARNING", "⚠️  Operación NO enviada a IQ Option (sin conexión real)")
            return None

        if self.api:
            try:
                resultado = self._llamar_con_timeout(
                    self.api.buy, monto, par, direccion.lower(), duracion
                )
                if resultado is None:
                    return None
                ok, order_id = resultado
                if ok:
                    log_event("INFO", f"Orden ejecutada (id={order_id})")
                    return order_id
                log_event("ERROR", f"IQ Option rechazó la compra: {order_id}")
            except Exception as exc:
                log_event("ERROR", f"Error ejecutando operación: {exc}")
        return None

    def _llamar_con_timeout(self, func, *args, timeout: int = 12):
        """Llama a una función de IQ Option con timeout para evitar bloqueos indefinidos."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(func, *args)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                log_event("ERROR", f"Timeout: IQ Option no respondió en {timeout}s")
                return None

    def resultado(self, order_id: Optional[object], modo: str, confianza: float, monto: float):
        """Resuelve el resultado de una operación ya vencida.

        Devuelve (resultado, ganancia): ('WIN'|'LOSE', float).
        order_id puede ser una tupla (tipo, id) o un id simple.
        """
        if not self.simulation and self.api and order_id is not None:
            try:
                profit = self.api.check_win_v4(order_id)
                if isinstance(profit, (tuple, list)):
                    profit = profit[-1]
                profit = float(profit)
                if profit > 0:
                    return "WIN", profit
                return "LOSE", -monto
            except Exception as exc:
                log_event("ERROR", f"No se pudo verificar resultado: {exc}. Resolviendo por simulación")
        # Simulación: probabilidad de ganar ponderada por la confianza del modelo
        prob_win = min(0.85, max(0.40, 0.45 + (confianza - 0.5) * 0.6))
        if random.random() < prob_win:
            return "WIN", round(monto * PAYOUT, 2)
        return "LOSE", -round(monto, 2)

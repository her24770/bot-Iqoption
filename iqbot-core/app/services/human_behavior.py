"""Anti-detección: delays aleatorios y límites para simular comportamiento humano."""
import random
import time
from datetime import datetime


def delay_antes_de_operar() -> float:
    """Simula tiempo de 'análisis humano' antes de ejecutar (2.5–7s)."""
    espera = random.uniform(2.5, 7.0)
    time.sleep(espera)
    return espera


def jitter_entre_sesiones() -> float:
    """Variación aleatoria (±30s) para el intervalo del scheduler."""
    return random.uniform(-30, 30)


def evitar_minuto_exacto() -> float:
    """Nunca operar exactamente en el minuto :00 (patrón de bot obvio).

    Si el análisis cae en el minuto :00, devuelve segundos extra (15–45) a esperar.
    """
    if datetime.utcnow().minute == 0:
        extra = random.uniform(15, 45)
        time.sleep(extra)
        return extra
    return 0.0

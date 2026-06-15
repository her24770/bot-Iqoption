"""Decisión final con GPT-4o mini. Responde CALL, PUT o SKIP en JSON."""
import json

from app.config import settings
from app.utils.logger import log_event

SYSTEM_PROMPT = """
Eres un analista de trading especializado en opciones binarias forex de 5 minutos.
Recibes datos técnicos de mercado y debes decidir: CALL, PUT o SKIP.
Responde ÚNICAMENTE con un JSON: {"decision": "CALL"|"PUT"|"SKIP", "razon": "string corto"}
No agregues nada más, sin markdown, sin explicaciones extra.
""".strip()


class GPTService:
    def __init__(self) -> None:
        self.client = None
        if not settings.OPENAI_API_KEY:
            log_event("INFO", "OPENAI_API_KEY no configurada: GPT desactivado")
            return
        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            log_event("INFO", "Cliente OpenAI inicializado correctamente")
        except Exception as exc:
            log_event(
                "ERROR",
                f"No se pudo inicializar el cliente OpenAI ({exc}). "
                "Verifica la versión de las librerías (httpx / openai).",
            )

    def decidir(self, contexto: dict) -> dict:
        """Devuelve {"decision": ..., "razon": ...}.

        Si GPT no está disponible, aprueba la dirección sugerida por los patrones.
        """
        if self.client is None:
            log_event(
                "WARNING",
                "GPT omitido: se aprueba la señal de los patrones",
            )
            return {"decision": contexto.get("direccion_sugerida", "SKIP"), "razon": "GPT desactivado"}

        user_prompt = self._construir_prompt(contexto)
        try:
            resp = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            contenido = resp.choices[0].message.content
            data = json.loads(contenido)
            decision = str(data.get("decision", "SKIP")).upper()
            if decision not in ("CALL", "PUT", "SKIP"):
                decision = "SKIP"
            return {"decision": decision, "razon": data.get("razon", "")}
        except Exception as exc:
            log_event("ERROR", f"Error en GPT (se omite la operación): {exc}")
            return {"decision": "SKIP", "razon": f"error: {exc}"}

    @staticmethod
    def _construir_prompt(c: dict) -> str:
        return f"""
Par: {c.get('par')}
Timeframe: 5 minutos
Timestamp: {c.get('timestamp')}

Indicadores actuales:
- RSI(14): {c.get('rsi')}
- EMA9: {c.get('ema9')} | EMA21: {c.get('ema21')} | Diferencia: {c.get('ema_diff')}
- Bollinger: inferior={c.get('bb_lower')}, media={c.get('bb_mid')}, superior={c.get('bb_upper')}
- Precio actual: {c.get('precio')}
- Volumen relativo: {c.get('vol_ratio')}x del promedio

Patrones detectados: {c.get('patrones_activos')}
Score XGBoost: {c.get('score')}% de confianza

Win rate histórico de estos patrones en mis últimas {c.get('n_ops')} operaciones: {c.get('win_rate_historico')}%

¿Ejecuto operación?
""".strip()

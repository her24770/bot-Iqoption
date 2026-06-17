"""Motor principal del bot: orquesta el ciclo de análisis cada 5 minutos.

Usa AsyncIOScheduler para compartir el event loop de FastAPI, de modo que el
broadcast de logs por WebSocket funcione desde los jobs.
"""
import uuid
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import SessionLocal
from app.models.configuracion import Configuracion
from app.models.operacion import Operacion
from app.redis_client import redis_client
from app.services import human_behavior
from app.services.config_cache import get_config_cache, sync_config_a_redis
from app.services.gpt_service import GPTService
from app.services.indicator_service import calcular_indicadores, snapshot_indicadores
from app.services.iqoption_service import IQOptionService
from app.services.ml_service import MLService
from app.services.pattern_service import detectar_patrones
from app.utils.logger import log_event

ESTADO_KEY = "bot:estado"
STREAK_KEY = "bot:perdidas_streak"
RATE_KEY = "rate_limit:ops"


class BotEngine:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.iq = IQOptionService()
        self.ml = MLService()
        self.gpt = GPTService()
        self._iniciado = False

    # --------------------------------------------------------------- arranque
    def iniciar(self) -> None:
        if self._iniciado:
            return
        self.iq.conectar()
        self.ml.cargar_o_entrenar()
        cfg = get_config_cache() or {}
        intervalo = int(cfg.get("intervalo_ciclo_minutos", 5))
        self.scheduler.add_job(
            self.ciclo,
            "interval",
            minutes=intervalo,
            id="ciclo_principal",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.start()
        self._iniciado = True
        log_event("INFO", f"Motor del bot iniciado (análisis cada {intervalo} minuto(s))")

    def reagendar_ciclo(self, minutos: int) -> None:
        """Cambia el intervalo del ciclo sin reiniciar el contenedor."""
        if not self.scheduler.running:
            return
        self.scheduler.reschedule_job(
            "ciclo_principal",
            trigger="interval",
            minutes=minutos,
        )
        log_event("INFO", f"Ciclo reprogramado: cada {minutos} minuto(s)")

    def detener_scheduler(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    # ------------------------------------------------------------ estado redis
    def _actualizar_estado(self, **kwargs) -> None:
        import json

        try:
            actual = redis_client.get(ESTADO_KEY)
            estado = json.loads(actual) if actual else {}
            estado.update(kwargs)
            redis_client.set(ESTADO_KEY, json.dumps(estado))
        except Exception:
            pass

    # ----------------------------------------------------------- ciclo principal
    async def ciclo(self) -> None:
        db = SessionLocal()
        try:
            cfg = get_config_cache()
            if cfg is None:
                config = db.query(Configuracion).get(1)
                if config is None:
                    return
                sync_config_a_redis(config)
                cfg = get_config_cache()

            if not cfg.get("activo"):
                return

            # Si hay credenciales pero la sesión de IQ Option se cayó, reconectar.
            # Si la reconexión falla, saltamos el ciclo para no guardar operaciones falsas.
            if self.iq.simulation and not self.iq.modo_simulacion_forzado:
                log_event("WARNING", "Conexión con IQ Option perdida. Intentando reconectar...")
                self.iq.reconectar()
                if self.iq.simulation:
                    log_event("ERROR", "No se pudo reconectar a IQ Option. Ciclo omitido.")
                    self._actualizar_estado(estado="sin_conexion")
                    return

            self._actualizar_estado(estado="analizando")

            ops_hora = int(redis_client.get(RATE_KEY) or 0)
            if ops_hora >= cfg["max_ops_por_hora"]:
                log_event("WARNING", f"Límite alcanzado: {ops_hora}/{cfg['max_ops_por_hora']} ops esta hora")
                self._actualizar_estado(estado="activo", ops_esta_hora=ops_hora)
                return

            par = cfg["par"]
            log_event("INFO", f"Analizando mercado {par}...")

            df = self.iq.obtener_velas(par, 50)
            df = calcular_indicadores(df)
            snap = snapshot_indicadores(df)

            log_event(
                "INFO",
                f"Indicadores: RSI={snap['rsi']:.1f} | "
                f"EMA diff={snap['ema_diff']:+.5f} | "
                f"Precio={snap['precio']:.5f} BB[{snap['bb_lower']:.5f}-{snap['bb_upper']:.5f}]",
            )

            patrones = detectar_patrones(df)
            if not patrones:
                log_event("INFO", "Sin señal: ningún patrón activo")
                self._actualizar_estado(estado="activo")
                return

            patron = patrones[0]
            features = {
                "rsi": snap["rsi"],
                "ema_diff": snap["ema_diff"],
                "bb_position": snap["bb_position"],
                "vol_ratio": snap["vol_ratio"],
                "patron_id": patron["id"],
                "hora_del_dia": datetime.utcnow().hour,
            }
            score = self.ml.score(features)
            log_event("INFO", f"Patrón '{patron['nombre']}' detectado. Confianza ML: {score:.0%}")

            if score < cfg["umbral_confianza"]:
                log_event("WARNING", f"Confianza insuficiente: {score:.0%} < {cfg['umbral_confianza']:.0%}")
                self._actualizar_estado(estado="activo")
                return

            # --- GPT decisión final ---
            n_ops = self._total_ops(db)
            win_rate_hist = self._win_rate_historico(db, patron["nombre"])
            contexto = {
                "par": par,
                "timestamp": datetime.utcnow().isoformat(),
                "rsi": round(snap["rsi"], 2),
                "ema9": round(snap["ema9"], 5),
                "ema21": round(snap["ema21"], 5),
                "ema_diff": round(snap["ema_diff"], 5),
                "bb_lower": round(snap["bb_lower"], 5),
                "bb_mid": round(snap["bb_mid"], 5),
                "bb_upper": round(snap["bb_upper"], 5),
                "precio": round(snap["precio"], 5),
                "vol_ratio": round(snap["vol_ratio"], 2),
                "patrones_activos": ", ".join(p["nombre"] for p in patrones),
                "score": round(score * 100, 1),
                "n_ops": n_ops,
                "win_rate_historico": win_rate_hist if n_ops > 0 else "sin historial previo",
                "direccion_sugerida": patron["direccion"],
            }
            decision_gpt = self.gpt.decidir(contexto)
            if decision_gpt["decision"] == "SKIP":
                log_event("WARNING", f"GPT recomienda no operar: {decision_gpt.get('razon', '')}")
                self._actualizar_estado(estado="activo")
                return

            direccion = decision_gpt["decision"]

            # --- Verificar que el mercado esté abierto ---
            if not self.iq.activo_disponible(par):
                log_event("INFO", f"Mercado cerrado para {par} en este momento. Esperando apertura.")
                self._actualizar_estado(estado="activo")
                return

            # --- Monto y anti-detección ---
            balance = self.iq.obtener_balance(cfg["modo"])
            monto = round(balance * cfg["monto_porcentaje_balance"], 2)
            human_behavior.evitar_minuto_exacto()
            human_behavior.delay_antes_de_operar()

            # --- Ejecutar ---
            order_id = self.iq.ejecutar(par, direccion, monto, cfg["modo"], duracion=5)

            # En modo real, si IQ Option rechaza la orden, no guardar operación falsa.
            if order_id is None and not self.iq.simulation and not self.iq.modo_simulacion_forzado:
                log_event("ERROR", "Operación rechazada por IQ Option. No se guardará en BD.")
                self._actualizar_estado(estado="activo")
                return

            ahora = datetime.utcnow()
            op = Operacion(
                id=uuid.uuid4(),
                par=par,
                direccion=direccion,
                monto=monto,
                resultado="PENDING",
                ganancia=0.0,
                patron_activado=patron["nombre"],
                confianza_ml=score,
                decision_gpt=decision_gpt["decision"],
                modo=cfg["modo"],
                indicadores_snapshot={**snap, "patron_id": patron["id"], "hora": ahora.hour},
                created_at=ahora,
                expires_at=ahora + timedelta(minutes=5),
            )
            db.add(op)
            db.commit()
            db.refresh(op)

            # Rate limit
            nuevo = redis_client.incr(RATE_KEY)
            if nuevo == 1:
                redis_client.expire(RATE_KEY, 3600)
            self._actualizar_estado(
                estado="activo",
                par=par,
                modo=cfg["modo"],
                ultima_operacion=ahora.isoformat(),
                ops_esta_hora=nuevo,
            )
            log_event("SUCCESS", f"Operación ejecutada: {direccion} ${monto} en {par} (orden {op.id})")

            # Programar la resolución del resultado al vencer la opción
            self.scheduler.add_job(
                self.resolver,
                "date",
                run_date=op.expires_at,
                args=[str(op.id), order_id],
                id=f"resolver_{op.id}",
                replace_existing=True,
            )
        except Exception as exc:
            log_event("ERROR", f"Error en el ciclo del bot: {exc}")
        finally:
            db.close()

    # ------------------------------------------------------ resolución resultado
    async def resolver(self, op_id: str, order_id) -> None:
        db = SessionLocal()
        try:
            op = db.query(Operacion).filter(Operacion.id == uuid.UUID(op_id)).first()
            if op is None or op.resultado != "PENDING":
                return

            resultado, ganancia = self.iq.resultado(order_id, op.modo, op.confianza_ml or 0.5, op.monto)
            op.resultado = resultado
            op.ganancia = ganancia
            db.commit()

            nivel = "SUCCESS" if resultado == "WIN" else "ERROR"
            log_event(nivel, f"Resultado {resultado}: ${ganancia} (orden {op_id})")

            cfg = get_config_cache() or {}
            if resultado == "LOSE":
                streak = redis_client.incr(STREAK_KEY)
                limite = cfg.get("perdidas_consecutivas_limite", 3)
                if streak >= limite:
                    self._desactivar_por_perdidas(db, streak)
            else:
                redis_client.set(STREAK_KEY, 0)

            # ¿Toca reentrenar?
            total = self._total_ops_cerradas(db)
            cada = cfg.get("reentrenar_cada_n_ops", 100)
            if cada and total > 0 and total % cada == 0:
                self._reentrenar(db, total)
        except Exception as exc:
            log_event("ERROR", f"Error resolviendo operación {op_id}: {exc}")
        finally:
            db.close()

    def _desactivar_por_perdidas(self, db, streak: int) -> None:
        config = db.query(Configuracion).get(1)
        if config:
            config.activo = False
            db.commit()
            sync_config_a_redis(config)
        self._actualizar_estado(estado="detenido", activo=False)
        log_event("ERROR", f"Bot detenido: {streak} pérdidas consecutivas")

    def _reentrenar(self, db, total: int) -> None:
        ops = (
            db.query(Operacion)
            .filter(Operacion.resultado.in_(["WIN", "LOSE"]))
            .all()
        )
        dataset = []
        for o in ops:
            snap = o.indicadores_snapshot or {}
            dataset.append({
                "snapshot": snap,
                "patron_id": snap.get("patron_id", 0),
                "hora": snap.get("hora", 0),
                "label": 1 if o.resultado == "WIN" else 0,
            })
        log_event("INFO", f"Reentrenando modelo con {total} operaciones...")
        self.ml.reentrenar(dataset)

    # ------------------------------------------------------------- helpers BD
    @staticmethod
    def _total_ops(db) -> int:
        return db.query(Operacion).count()

    @staticmethod
    def _total_ops_cerradas(db) -> int:
        return db.query(Operacion).filter(Operacion.resultado.in_(["WIN", "LOSE"])).count()

    @staticmethod
    def _win_rate_historico(db, patron: str) -> float:
        q = db.query(Operacion).filter(
            Operacion.patron_activado == patron,
            Operacion.resultado.in_(["WIN", "LOSE"]),
        )
        total = q.count()
        if total == 0:
            return 0.0
        wins = q.filter(Operacion.resultado == "WIN").count()
        return round(wins / total * 100, 1)


# Instancia única del motor
bot_engine = BotEngine()

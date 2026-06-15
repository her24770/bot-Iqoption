import { useEffect, useState } from 'react'
import api from '../services/api'

const PARES = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']

// Panel colapsable de configuración en vivo
export default function ConfigPanel() {
  const [abierto, setAbierto] = useState(false)
  const [config, setConfig] = useState(null)
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  useEffect(() => {
    api.get('/config').then(({ data }) => setConfig(data)).catch(() => {})
  }, [])

  const set = (campo, valor) => setConfig((c) => ({ ...c, [campo]: valor }))

  const guardar = async () => {
    setGuardando(true)
    setMensaje('')
    try {
      const { data } = await api.put('/config', {
        par: config.par,
        umbral_confianza: Number(config.umbral_confianza),
        max_ops_por_hora: Number(config.max_ops_por_hora),
        monto_porcentaje_balance: Number(config.monto_porcentaje_balance),
        perdidas_consecutivas_limite: Number(config.perdidas_consecutivas_limite),
        reentrenar_cada_n_ops: Number(config.reentrenar_cada_n_ops),
        intervalo_ciclo_minutos: Number(config.intervalo_ciclo_minutos),
      })
      setConfig(data)
      setMensaje('Cambios aplicados ✓')
    } catch {
      setMensaje('Error al guardar')
    } finally {
      setGuardando(false)
      setTimeout(() => setMensaje(''), 3000)
    }
  }

  if (!config) return null

  return (
    <div className="rounded-2xl bg-panel p-5">
      <button
        onClick={() => setAbierto((a) => !a)}
        className="flex w-full items-center justify-between text-sm text-gray-400"
      >
        <span>Configuración en vivo</span>
        <span>{abierto ? '▲' : '▼'}</span>
      </button>

      {abierto && (
        <div className="mt-5 space-y-5">
          <Slider
            label={`Intervalo de análisis: cada ${config.intervalo_ciclo_minutos} minuto(s)`}
            min={1}
            max={30}
            step={1}
            value={config.intervalo_ciclo_minutos ?? 5}
            onChange={(v) => set('intervalo_ciclo_minutos', v)}
          />

          <Campo label="Par de divisas">
            <select
              value={config.par}
              onChange={(e) => set('par', e.target.value)}
              className="w-full rounded-lg bg-base px-3 py-2 ring-1 ring-gray-700"
            >
              {PARES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </Campo>

          <Slider
            label={`Umbral de confianza mínimo: ${Math.round(config.umbral_confianza * 100)}%`}
            min={0.1}
            max={0.95}
            step={0.01}
            value={config.umbral_confianza}
            onChange={(v) => set('umbral_confianza', v)}
          />

          <Campo label="Máx. operaciones por hora">
            <input
              type="number"
              min={1}
              value={config.max_ops_por_hora}
              onChange={(e) => set('max_ops_por_hora', e.target.value)}
              className="w-full rounded-lg bg-base px-3 py-2 ring-1 ring-gray-700"
            />
          </Campo>

          <Slider
            label={`% del balance por operación: ${Math.round(config.monto_porcentaje_balance * 100)}%`}
            min={0.01}
            max={0.1}
            step={0.005}
            value={config.monto_porcentaje_balance}
            onChange={(v) => set('monto_porcentaje_balance', v)}
          />

          <Campo label="Límite de pérdidas consecutivas">
            <input
              type="number"
              min={1}
              value={config.perdidas_consecutivas_limite}
              onChange={(e) => set('perdidas_consecutivas_limite', e.target.value)}
              className="w-full rounded-lg bg-base px-3 py-2 ring-1 ring-gray-700"
            />
          </Campo>

          <Campo label="Reentrenar modelo cada N operaciones">
            <input
              type="number"
              min={10}
              value={config.reentrenar_cada_n_ops}
              onChange={(e) => set('reentrenar_cada_n_ops', e.target.value)}
              className="w-full rounded-lg bg-base px-3 py-2 ring-1 ring-gray-700"
            />
          </Campo>

          <div className="flex items-center gap-3">
            <button
              onClick={guardar}
              disabled={guardando}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold disabled:opacity-50"
            >
              {guardando ? 'Guardando…' : 'Guardar cambios'}
            </button>
            {mensaje && <span className="text-sm text-green-400">{mensaje}</span>}
          </div>
        </div>
      )}
    </div>
  )
}

function Campo({ label, children }) {
  return (
    <div>
      <label className="mb-1 block text-xs text-gray-400">{label}</label>
      {children}
    </div>
  )
}

function Slider({ label, value, onChange, min, max, step }) {
  return (
    <div>
      <label className="mb-1 block text-xs text-gray-400">{label}</label>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-blue-500"
      />
    </div>
  )
}

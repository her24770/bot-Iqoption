import { useState } from 'react'
import api from '../services/api'

const PARES_MANUAL = ['EURUSD', 'EURUSD-OTC', 'GBPUSD', 'GBPUSD-OTC', 'USDJPY-OTC']

export default function ManualTrade({ par: parProp = 'EURUSD' }) {
  const [par, setPar] = useState(parProp)
  const [cargando, setCargando] = useState(null)
  const [resultado, setResultado] = useState(null)

  const operar = async (direccion) => {
    setCargando(direccion)
    setResultado(null)
    try {
      const { data } = await api.post('/bot/operar-manual', { direccion, par }, { timeout: 20000 })
      setResultado({ ok: data.ok, mensaje: data.mensaje })
    } catch (e) {
      setResultado({ ok: false, mensaje: e.response?.data?.detail || 'Error de conexión' })
    } finally {
      setCargando(null)
      setTimeout(() => setResultado(null), 8000)
    }
  }

  return (
    <div className="rounded-2xl bg-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm font-semibold text-white">Operación manual</p>
        <select
          value={par}
          onChange={(e) => setPar(e.target.value)}
          className="rounded-lg bg-base px-3 py-1 text-sm ring-1 ring-gray-700"
        >
          {PARES_MANUAL.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => operar('CALL')}
          disabled={!!cargando}
          className="flex-1 rounded-xl bg-green-600 py-3 text-sm font-bold tracking-wide hover:bg-green-500 disabled:opacity-40"
        >
          {cargando === 'CALL' ? '…' : '▲ CALL'}
        </button>

        <button
          onClick={() => operar('PUT')}
          disabled={!!cargando}
          className="flex-1 rounded-xl bg-red-600 py-3 text-sm font-bold tracking-wide hover:bg-red-500 disabled:opacity-40"
        >
          {cargando === 'PUT' ? '…' : '▼ PUT'}
        </button>
      </div>

      {resultado && (
        <p className={`mt-3 text-sm ${resultado.ok ? 'text-green-400' : 'text-red-400'}`}>
          {resultado.ok ? '✓' : '✗'} {resultado.mensaje}
        </p>
      )}
    </div>
  )
}

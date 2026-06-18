import { useState } from 'react'
import api from '../services/api'

export default function ManualTrade({ par = 'EURUSD' }) {
  const [cargando, setCargando] = useState(null) // 'CALL' | 'PUT' | null
  const [resultado, setResultado] = useState(null)

  const operar = async (direccion) => {
    setCargando(direccion)
    setResultado(null)
    try {
      const { data } = await api.post('/bot/operar-manual', { direccion, par })
      setResultado({ ok: data.ok, mensaje: data.mensaje })
    } catch (e) {
      setResultado({ ok: false, mensaje: e.response?.data?.detail || 'Error de conexión' })
    } finally {
      setCargando(null)
      setTimeout(() => setResultado(null), 6000)
    }
  }

  return (
    <div className="rounded-2xl bg-panel p-5">
      <p className="mb-4 text-sm text-gray-400">Operación manual — {par}</p>

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

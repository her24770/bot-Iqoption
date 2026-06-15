import { useMemo, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

// Gráfica de P&L acumulado con filtro de rango
export default function RendimientoChart({ stats }) {
  const [rango, setRango] = useState('todo')
  const datos = stats?.rendimiento || []

  const filtrados = useMemo(() => {
    if (rango === 'todo') return datos
    const dias = rango === '7d' ? 7 : 30
    return datos.slice(-dias)
  }, [datos, rango])

  return (
    <div className="rounded-2xl bg-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-400">Rendimiento acumulado (P&L)</p>
        <div className="flex gap-1 text-xs">
          {['7d', '30d', 'todo'].map((r) => (
            <button
              key={r}
              onClick={() => setRango(r)}
              className={`rounded px-2 py-1 ${rango === r ? 'bg-accent text-white' : 'text-gray-400'}`}
            >
              {r === 'todo' ? 'Todo' : r}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={filtrados}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="fecha" stroke="#6b7280" fontSize={11} />
          <YAxis stroke="#6b7280" fontSize={11} />
          <Tooltip
            contentStyle={{ background: '#141a26', border: '1px solid #374151', borderRadius: 8 }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <Line type="monotone" dataKey="pnl_acumulado" stroke="#3b82f6" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>

      {filtrados.length === 0 && (
        <p className="py-8 text-center text-sm text-gray-500">Aún no hay operaciones cerradas</p>
      )}
    </div>
  )
}

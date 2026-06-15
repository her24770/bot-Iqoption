import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useBot } from '../hooks/useBot'
import StatusCard from '../components/StatusCard'
import BalanceCard from '../components/BalanceCard'
import BotControls from '../components/BotControls'
import StatsCards from '../components/StatsCards'
import RendimientoChart from '../components/RendimientoChart'
import PatternStats from '../components/PatternStats'
import ConfigPanel from '../components/ConfigPanel'
import OperacionesTable from '../components/OperacionesTable'
import LogsPanel from '../components/LogsPanel'

export default function Dashboard() {
  const { usuario, logout } = useAuth()
  const { status, start, stop, cambiarModo } = useBot()
  const [stats, setStats] = useState(null)

  useEffect(() => {
    const cargar = () => api.get('/operaciones/stats').then(({ data }) => setStats(data)).catch(() => {})
    cargar()
    const id = setInterval(cargar, 8000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-gray-800 bg-base/90 px-6 py-4 backdrop-blur">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-accent">IQBot</h1>
          <StatusCard status={status} />
        </div>
        <div className="flex items-center gap-4">
          <span
            className={`rounded-lg px-3 py-1 text-xs font-semibold ${
              status?.modo === 'real' ? 'bg-red-600' : 'bg-blue-600'
            }`}
          >
            {status?.modo?.toUpperCase() || 'DEMO'}
          </span>
          <span className="hidden text-sm text-gray-400 sm:inline">{usuario?.email}</span>
          <button onClick={logout} className="rounded-lg bg-gray-700 px-3 py-1 text-sm hover:bg-gray-600">
            Salir
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-6 py-6">
        {/* Control + Balance */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <BotControls status={status} onStart={start} onStop={stop} onCambiarModo={cambiarModo} />
          <BalanceCard status={status} />
          <div className="rounded-2xl bg-panel p-5">
            <p className="text-sm text-gray-400">Par operando</p>
            <p className="mt-1 text-3xl font-bold text-white">{status?.par || '—'}</p>
            <p className="mt-1 text-xs text-gray-500">Última op: {status?.ultima_operacion ? new Date(status.ultima_operacion + 'Z').toLocaleTimeString('es') : '—'}</p>
          </div>
        </div>

        {/* Stats */}
        <StatsCards stats={stats} status={status} />

        {/* Gráfica + Patrones */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <RendimientoChart stats={stats} />
          </div>
          <PatternStats stats={stats} />
        </div>

        {/* Configuración */}
        <ConfigPanel />

        {/* Historial */}
        <OperacionesTable />

        {/* Logs */}
        <LogsPanel />
      </main>
    </div>
  )
}

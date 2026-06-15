// 4 tarjetas de métricas: Win Rate, Total ops, P&L, Ops esta hora
function Card({ titulo, valor, sub, color = 'text-white' }) {
  return (
    <div className="rounded-2xl bg-panel p-5">
      <p className="text-sm text-gray-400">{titulo}</p>
      <p className={`mt-1 text-2xl font-bold ${color}`}>{valor}</p>
      {sub && <p className="mt-1 text-xs text-gray-500">{sub}</p>}
    </div>
  )
}

export default function StatsCards({ stats, status }) {
  const pnl = stats?.pnl_total ?? 0
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <Card titulo="Win Rate" valor={`${stats?.win_rate ?? 0}%`} sub={`${stats?.wins ?? 0} ganadas`} color="text-green-400" />
      <Card titulo="Total operaciones" valor={stats?.total_operaciones ?? 0} />
      <Card
        titulo="P&L acumulado"
        valor={`$${pnl.toLocaleString('es', { minimumFractionDigits: 2 })}`}
        color={pnl >= 0 ? 'text-green-400' : 'text-red-400'}
      />
      <Card
        titulo="Ops esta hora"
        valor={`${status?.ops_esta_hora ?? 0} / ${status?.max_ops_por_hora ?? 0}`}
      />
    </div>
  )
}

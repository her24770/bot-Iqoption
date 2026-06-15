// Balance en tiempo real
export default function BalanceCard({ status }) {
  const balance = status?.balance ?? 0
  return (
    <div className="rounded-2xl bg-panel p-5">
      <p className="text-sm text-gray-400">Balance actual</p>
      <p className="mt-1 text-3xl font-bold text-white">
        ${balance.toLocaleString('es', { minimumFractionDigits: 2 })}
      </p>
      <p className="mt-1 text-xs text-gray-500">Modo {status?.modo?.toUpperCase() || '—'}</p>
    </div>
  )
}

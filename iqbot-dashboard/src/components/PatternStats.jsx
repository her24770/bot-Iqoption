// Win rate por patrón en barras
export default function PatternStats({ stats }) {
  const patrones = stats?.por_patron || []

  return (
    <div className="rounded-2xl bg-panel p-5">
      <p className="mb-4 text-sm text-gray-400">Win rate por patrón</p>
      {patrones.length === 0 && (
        <p className="text-sm text-gray-500">Sin datos todavía</p>
      )}
      <div className="space-y-4">
        {patrones.map((p) => (
          <div key={p.patron}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="text-gray-300">{p.patron}</span>
              <span className="text-gray-400">
                {p.win_rate}% ({p.wins}/{p.total})
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-base">
              <div
                className="h-full rounded-full bg-accent"
                style={{ width: `${p.win_rate}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

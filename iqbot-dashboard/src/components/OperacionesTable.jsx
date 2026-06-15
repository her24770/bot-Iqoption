import { useEffect, useState } from 'react'
import api, { API_URL } from '../services/api'

// Historial de operaciones con paginación
export default function OperacionesTable() {
  const [data, setData] = useState({ items: [], total: 0 })
  const [page, setPage] = useState(1)
  const limit = 10

  const cargar = async () => {
    try {
      const { data } = await api.get('/operaciones', { params: { page, limit } })
      setData(data)
    } catch {
      // ignora
    }
  }

  useEffect(() => {
    cargar()
    const id = setInterval(cargar, 8000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  const totalPaginas = Math.max(1, Math.ceil(data.total / limit))

  const colorResultado = (r) =>
    r === 'WIN' ? 'text-green-400' : r === 'LOSE' ? 'text-red-400' : 'text-yellow-400'

  const exportar = () => {
    const token = localStorage.getItem('token')
    fetch(`${API_URL}/operaciones/export/csv`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'operaciones.csv'
        a.click()
        URL.revokeObjectURL(url)
      })
  }

  return (
    <div className="rounded-2xl bg-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-400">Historial de operaciones</p>
        <button onClick={exportar} className="rounded bg-gray-700 px-3 py-1 text-xs hover:bg-gray-600">
          Exportar CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-gray-500">
            <tr>
              <th className="py-2 pr-4">Fecha</th>
              <th className="py-2 pr-4">Par</th>
              <th className="py-2 pr-4">Dir.</th>
              <th className="py-2 pr-4">Monto</th>
              <th className="py-2 pr-4">Resultado</th>
              <th className="py-2 pr-4">Ganancia</th>
              <th className="py-2 pr-4">Patrón</th>
              <th className="py-2 pr-4">Conf. ML</th>
              <th className="py-2 pr-4">GPT</th>
            </tr>
          </thead>
          <tbody className="text-gray-300">
            {data.items.map((op) => (
              <tr key={op.id} className="border-t border-gray-800">
                <td className="py-2 pr-4 text-xs text-gray-400">
                  {new Date(op.created_at).toLocaleString('es')}
                </td>
                <td className="py-2 pr-4">{op.par}</td>
                <td className="py-2 pr-4">{op.direccion}</td>
                <td className="py-2 pr-4">${op.monto}</td>
                <td className={`py-2 pr-4 font-semibold ${colorResultado(op.resultado)}`}>
                  {op.resultado}
                </td>
                <td className={`py-2 pr-4 ${op.ganancia >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${op.ganancia}
                </td>
                <td className="py-2 pr-4 text-xs">{op.patron_activado}</td>
                <td className="py-2 pr-4">
                  {op.confianza_ml != null ? `${Math.round(op.confianza_ml * 100)}%` : '—'}
                </td>
                <td className="py-2 pr-4">{op.decision_gpt}</td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr>
                <td colSpan={9} className="py-6 text-center text-gray-500">
                  Sin operaciones aún
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-gray-500">
          {data.total} operaciones · página {page}/{totalPaginas}
        </span>
        <div className="flex gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded bg-gray-700 px-3 py-1 disabled:opacity-40"
          >
            Anterior
          </button>
          <button
            disabled={page >= totalPaginas}
            onClick={() => setPage((p) => p + 1)}
            className="rounded bg-gray-700 px-3 py-1 disabled:opacity-40"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  )
}

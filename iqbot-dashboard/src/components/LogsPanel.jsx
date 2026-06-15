import { useEffect, useRef } from 'react'
import { useLogs } from '../hooks/useLogs'

const COLOR_NIVEL = {
  INFO: 'text-gray-200',
  WARNING: 'text-yellow-400',
  ERROR: 'text-red-400',
  SUCCESS: 'text-green-400',
}

// Terminal de logs en tiempo real con auto-scroll y reconexión
export default function LogsPanel() {
  const { logs, conectado, limpiar } = useLogs()
  const finRef = useRef(null)

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="rounded-2xl bg-panel p-5">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <p className="text-sm text-gray-400">Logs en tiempo real</p>
          <span
            className={`inline-block h-2 w-2 rounded-full ${conectado ? 'bg-green-500' : 'bg-red-500'}`}
            title={conectado ? 'Conectado' : 'Desconectado'}
          />
        </div>
        <button onClick={limpiar} className="rounded bg-gray-700 px-3 py-1 text-xs hover:bg-gray-600">
          Limpiar
        </button>
      </div>

      <div className="h-72 overflow-y-auto rounded-lg bg-black p-3 font-mono text-xs">
        {logs.length === 0 && <p className="text-gray-600">Esperando logs…</p>}
        {logs.map((log, i) => (
          <div key={i} className={COLOR_NIVEL[log.level] || 'text-gray-300'}>
            <span className="text-gray-600">
              {new Date(log.timestamp + 'Z').toLocaleTimeString('es')}
            </span>{' '}
            [{log.level}] {log.message}
          </div>
        ))}
        <div ref={finRef} />
      </div>
    </div>
  )
}

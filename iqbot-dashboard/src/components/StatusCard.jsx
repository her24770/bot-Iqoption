// Indicador de estado del bot (verde=activo, rojo=detenido, amarillo=analizando)
const COLORES = {
  activo: 'bg-green-500',
  analizando: 'bg-yellow-400',
  detenido: 'bg-red-500',
}

export default function StatusCard({ status }) {
  const estado = status?.estado || 'detenido'
  const color = COLORES[estado] || 'bg-gray-500'

  return (
    <div className="flex items-center gap-3">
      <span className={`inline-block h-3 w-3 rounded-full ${color} animate-pulse`} />
      <span className="text-sm capitalize text-gray-300">{estado}</span>
      {status?.simulacion && (
        <span className="rounded bg-purple-900/50 px-2 py-0.5 text-xs text-purple-300">
          SIMULACIÓN
        </span>
      )}
    </div>
  )
}

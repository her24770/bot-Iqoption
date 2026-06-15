import { useState } from 'react'

// Control principal: toggle ON/OFF + switch DEMO/REAL con confirmación
export default function BotControls({ status, onStart, onStop, onCambiarModo }) {
  const [confirmando, setConfirmando] = useState(false)
  const activo = status?.activo
  const modo = status?.modo || 'demo'

  const toggle = () => (activo ? onStop() : onStart())

  const pedirCambioModo = (nuevoModo) => {
    if (nuevoModo === 'real') {
      setConfirmando(true)
    } else {
      onCambiarModo('demo')
    }
  }

  return (
    <div className="rounded-2xl bg-panel p-5">
      <p className="mb-4 text-sm text-gray-400">Control principal</p>

      <button
        onClick={toggle}
        className={`mb-5 w-full rounded-xl py-4 text-lg font-bold transition ${
          activo
            ? 'bg-red-600 hover:bg-red-700'
            : 'bg-green-600 hover:bg-green-700'
        }`}
      >
        {activo ? 'APAGAR BOT' : 'ENCENDER BOT'}
      </button>

      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">Modo de cuenta</span>
        <div className="flex overflow-hidden rounded-lg ring-1 ring-gray-700">
          <button
            onClick={() => pedirCambioModo('demo')}
            className={`px-4 py-1.5 text-sm ${modo === 'demo' ? 'bg-accent text-white' : 'text-gray-400'}`}
          >
            DEMO
          </button>
          <button
            onClick={() => pedirCambioModo('real')}
            className={`px-4 py-1.5 text-sm ${modo === 'real' ? 'bg-red-600 text-white' : 'text-gray-400'}`}
          >
            REAL
          </button>
        </div>
      </div>

      {confirmando && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-sm rounded-2xl bg-panel p-6">
            <h3 className="mb-2 text-lg font-bold text-red-400">¿Cambiar a modo REAL?</h3>
            <p className="mb-5 text-sm text-gray-300">
              El bot operará con dinero real. Asegúrate de tu configuración antes de continuar.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmando(false)}
                className="flex-1 rounded-lg bg-gray-700 py-2 text-sm"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  onCambiarModo('real')
                  setConfirmando(false)
                }}
                className="flex-1 rounded-lg bg-red-600 py-2 text-sm font-semibold"
              >
                Sí, cambiar a REAL
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

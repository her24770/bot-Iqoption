import { useCallback, useEffect, useState } from 'react'
import api from '../services/api'

// Hook para el estado del bot, con polling cada 5s
export function useBot() {
  const [status, setStatus] = useState(null)
  const [cargando, setCargando] = useState(true)

  const refrescar = useCallback(async () => {
    try {
      const { data } = await api.get('/bot/status')
      setStatus(data)
    } catch {
      // silencioso; el interceptor maneja 401
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    refrescar()
    const id = setInterval(refrescar, 5000)
    return () => clearInterval(id)
  }, [refrescar])

  const start = async () => {
    await api.post('/bot/start')
    await refrescar()
  }

  const stop = async () => {
    await api.post('/bot/stop')
    await refrescar()
  }

  const cambiarModo = async (modo) => {
    await api.put('/config', { modo })
    await refrescar()
  }

  return { status, cargando, refrescar, start, stop, cambiarModo }
}

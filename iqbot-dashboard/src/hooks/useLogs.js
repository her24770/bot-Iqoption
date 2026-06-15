import { useEffect, useRef, useState } from 'react'
import { wsLogsUrl } from '../services/ws'

// Hook de logs en tiempo real con reconexión automática del WebSocket
export function useLogs() {
  const [logs, setLogs] = useState([])
  const [conectado, setConectado] = useState(false)
  const wsRef = useRef(null)
  const reconnectRef = useRef(null)

  useEffect(() => {
    let cerrado = false

    function conectar() {
      const token = localStorage.getItem('token')
      if (!token) return

      const ws = new WebSocket(wsLogsUrl(token))
      wsRef.current = ws

      ws.onopen = () => setConectado(true)

      ws.onmessage = (evt) => {
        try {
          const entry = JSON.parse(evt.data)
          setLogs((prev) => [...prev.slice(-300), entry])
        } catch {
          // ignora mensajes no JSON
        }
      }

      ws.onclose = () => {
        setConectado(false)
        if (!cerrado) {
          // Reconexión automática tras 3s
          reconnectRef.current = setTimeout(conectar, 3000)
        }
      }

      ws.onerror = () => ws.close()
    }

    conectar()

    return () => {
      cerrado = true
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  const limpiar = () => setLogs([])

  return { logs, conectado, limpiar }
}

import { API_URL } from './api'

// Convierte http(s)://host a ws(s)://host para el WebSocket de logs
export function wsLogsUrl(token) {
  const base = API_URL.replace(/^http/, 'ws')
  return `${base}/ws/logs?token=${encodeURIComponent(token)}`
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      const msg = err?.response?.data?.detail?.message || 'No se pudo iniciar sesión'
      setError(msg)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="flex h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm rounded-2xl bg-panel p-8 shadow-xl">
        <h1 className="mb-1 text-2xl font-bold text-accent">IQBot</h1>
        <p className="mb-6 text-sm text-gray-400">Panel de administración</p>

        {error && (
          <div className="mb-4 rounded-lg bg-red-900/40 px-3 py-2 text-sm text-red-300">{error}</div>
        )}

        <label className="mb-2 block text-sm text-gray-300">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="mb-4 w-full rounded-lg bg-base px-3 py-2 text-gray-100 outline-none ring-1 ring-gray-700 focus:ring-accent"
        />

        <label className="mb-2 block text-sm text-gray-300">Contraseña</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="mb-6 w-full rounded-lg bg-base px-3 py-2 text-gray-100 outline-none ring-1 ring-gray-700 focus:ring-accent"
        />

        <button
          type="submit"
          disabled={cargando}
          className="w-full rounded-lg bg-accent py-2 font-semibold text-white transition hover:bg-blue-600 disabled:opacity-50"
        >
          {cargando ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}

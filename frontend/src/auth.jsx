import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [carregando, setCarregando] = useState(Boolean(getToken()))

  useEffect(() => {
    if (!getToken()) return
    api('/auth/eu/')
      .then(setUsuario)
      .catch(() => setToken(null))
      .finally(() => setCarregando(false))
  }, [])

  useEffect(() => {
    const expirou = () => setUsuario(null)
    window.addEventListener('nf:sessao-expirada', expirou)
    return () => window.removeEventListener('nf:sessao-expirada', expirou)
  }, [])

  const entrar = useCallback(async (email, senha) => {
    const r = await api('/auth/login/', { method: 'POST', body: { email, senha } })
    setToken(r.token)
    setUsuario(r.usuario)
    return r.usuario
  }, [])

  const cadastrar = useCallback(async (dados) => {
    const r = await api('/auth/registro/', { method: 'POST', body: dados })
    setToken(r.token)
    setUsuario(r.usuario)
    return r.usuario
  }, [])

  const sair = useCallback(async () => {
    try {
      await api('/auth/logout/', { method: 'POST' })
    } catch {
      /* token já inválido */
    }
    setToken(null)
    setUsuario(null)
  }, [])

  return (
    <AuthContext.Provider value={{ usuario, carregando, entrar, cadastrar, sair }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

export const rotaInicial = (u) =>
  !u ? '/login' : u.tipo === 'CLIENTE' ? '/pedidos' : u.tipo === 'DESIGNER' ? '/projetos' : '/ordens-disponiveis'

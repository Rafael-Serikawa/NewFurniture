// Roteador mínimo baseado no hash da URL (#/pedidos/12).
// Evita dependências extras e funciona tanto no Vite quanto servido pelo Django.
import { useEffect, useState } from 'react'

const caminhoAtual = () => window.location.hash.replace(/^#/, '') || '/'

export function useRota() {
  const [caminho, setCaminho] = useState(caminhoAtual)
  useEffect(() => {
    const atualizar = () => {
      setCaminho(caminhoAtual())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', atualizar)
    return () => window.removeEventListener('hashchange', atualizar)
  }, [])
  return caminho
}

export function navegar(para) {
  if (caminhoAtual() === para) window.dispatchEvent(new HashChangeEvent('hashchange'))
  else window.location.hash = para
}

export function Link({ para, children, ...resto }) {
  return (
    <a href={`#${para}`} {...resto}>
      {children}
    </a>
  )
}

// casa um padrão ("/pedidos/:id") com o caminho e devolve os parâmetros
export function casar(padrao, caminho) {
  const [semQuery] = caminho.split('?')
  const p = padrao.split('/').filter(Boolean)
  const c = semQuery.split('/').filter(Boolean)
  if (p.length !== c.length) return null
  const params = {}
  for (let i = 0; i < p.length; i++) {
    if (p[i].startsWith(':')) params[p[i].slice(1)] = decodeURIComponent(c[i])
    else if (p[i] !== c[i]) return null
  }
  return params
}

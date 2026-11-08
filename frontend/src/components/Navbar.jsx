import { useEffect, useRef, useState } from 'react'
import { api, dataHora } from '../api'
import { useAuth } from '../auth'
import { Link, navegar } from '../router'
import { Avatar, Icone } from './ui'

export function Logo({ claro = true }) {
  return (
    <span className={`logo ${claro ? 'claro' : ''}`}>
      <svg viewBox="0 0 64 64" width="30" height="30" aria-hidden="true">
        <rect width="64" height="64" rx="14" fill={claro ? '#fff' : '#BA8850'} />
        <path
          d="M21 12v38M21 33h22M43 33v17M21 33l-1 0"
          fill="none"
          stroke={claro ? '#BA8850' : '#fff'}
          strokeWidth="5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>
        New<b>Furniture</b>
      </span>
    </span>
  )
}

const MENUS = {
  CLIENTE: [
    ['/pedidos', 'Meus pedidos'],
    ['/historico', 'Histórico'],
    ['/orcamentos', 'Orçamentos'],
  ],
  DESIGNER: [
    ['/projetos', 'Projetos disponíveis'],
    ['/minhas-propostas', 'Minhas propostas'],
    ['/historico', 'Histórico'],
    ['/orcamentos', 'Orçamentos'],
  ],
  MARCENEIRO: [
    ['/ordens-disponiveis', 'Projetos disponíveis'],
    ['/meus-projetos', 'Meus projetos'],
    ['/historico', 'Histórico'],
    ['/orcamentos', 'Orçamentos'],
  ],
}

function Notificacoes() {
  const [dados, setDados] = useState({ nao_lidas: 0, itens: [] })
  const [aberto, setAberto] = useState(false)
  const ref = useRef(null)

  const carregar = () => api('/notificacoes/').then(setDados).catch(() => {})
  useEffect(() => {
    carregar()
    const t = setInterval(carregar, 20000)
    const atualizar = () => carregar()
    window.addEventListener('nf:atualizar-notificacoes', atualizar)
    return () => {
      clearInterval(t)
      window.removeEventListener('nf:atualizar-notificacoes', atualizar)
    }
  }, [])
  useEffect(() => {
    const fora = (e) => ref.current && !ref.current.contains(e.target) && setAberto(false)
    document.addEventListener('mousedown', fora)
    return () => document.removeEventListener('mousedown', fora)
  }, [])

  const abrir = async (n) => {
    setAberto(false)
    if (!n.lida) await api(`/notificacoes/${n.id}/lida/`, { method: 'POST' }).catch(() => {})
    carregar()
    if (n.link) navegar(n.link)
  }
  const lerTodas = async () => {
    await api('/notificacoes/marcar-todas/', { method: 'POST' }).catch(() => {})
    carregar()
  }

  return (
    <div className="notificacoes" ref={ref}>
      <button className="botao-sino" onClick={() => setAberto((a) => !a)} aria-label="Notificações">
        <Icone.sino />
        {dados.nao_lidas > 0 && <span className="sino-contador">{dados.nao_lidas}</span>}
      </button>
      {aberto && (
        <div className="dropdown dropdown-notificacoes">
          <div className="dropdown-topo">
            <strong>Notificações</strong>
            {dados.nao_lidas > 0 && (
              <button className="link" onClick={lerTodas}>
                marcar todas como lidas
              </button>
            )}
          </div>
          {dados.itens.length === 0 && <p className="dropdown-vazio">Nenhuma notificação.</p>}
          {dados.itens.map((n) => (
            <button key={n.id} className={`notificacao ${n.lida ? '' : 'nao-lida'}`} onClick={() => abrir(n)}>
              <span>{n.mensagem}</span>
              <small>{dataHora(n.criada_em)}</small>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Navbar({ caminho }) {
  const { usuario, sair } = useAuth()
  const [menuAberto, setMenuAberto] = useState(false)
  const [mobile, setMobile] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    const fora = (e) => ref.current && !ref.current.contains(e.target) && setMenuAberto(false)
    document.addEventListener('mousedown', fora)
    return () => document.removeEventListener('mousedown', fora)
  }, [])
  useEffect(() => setMobile(false), [caminho])

  const itens = [['/sobre', 'Sobre'], ...(usuario ? MENUS[usuario.tipo] || [] : [])]
  const ativo = (rota) => caminho === rota || caminho.startsWith(rota + '/')

  return (
    <header className="navbar">
      <div className="navbar-conteudo">
        <Link para="/" className="navbar-logo">
          <Logo />
        </Link>
        <button className="navbar-hamburguer" onClick={() => setMobile((m) => !m)} aria-label="Menu">
          ☰
        </button>
        <nav className={`navbar-links ${mobile ? 'aberto' : ''}`}>
          {itens.map(([rota, rotulo]) => (
            <Link key={rota} para={rota} className={ativo(rota) ? 'ativo' : ''}>
              {rotulo}
            </Link>
          ))}
        </nav>
        <div className="navbar-direita">
          {usuario ? (
            <>
              <Notificacoes />
              <div className="perfil" ref={ref}>
                <button className="perfil-botao" onClick={() => setMenuAberto((a) => !a)}>
                  <span className="perfil-papel">{usuario.tipo_display}</span>
                  <Avatar nome={usuario.nome} />
                </button>
                {menuAberto && (
                  <div className="dropdown dropdown-perfil">
                    <div className="perfil-info">
                      <strong>{usuario.nome}</strong>
                      <small>{usuario.email}</small>
                      {usuario.cidade && <small>{usuario.cidade}</small>}
                    </div>
                    <button
                      className="item-menu"
                      onClick={async () => {
                        await sair()
                        navegar('/login')
                      }}
                    >
                      Sair
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <Link para="/login" className="botao botao-claro">
              Entrar
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}

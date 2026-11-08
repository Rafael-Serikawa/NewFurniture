import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { ehPdf } from '../api'

// ------------------------------------------------------------------ ícones
export const Icone = {
  imagem: (p) => (
    <svg viewBox="0 0 24 24" width="44" height="44" {...p}>
      <rect x="2.5" y="4" width="19" height="16" rx="1.5" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="8" cy="9.5" r="1.8" fill="currentColor" />
      <path d="M4 18l5-5.5 3.5 3.5 2.5-2.5L20 18z" fill="currentColor" />
    </svg>
  ),
  mais: (p) => (
    <svg viewBox="0 0 24 24" width="28" height="28" {...p}>
      <path d="M12 4v16M4 12h16" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" />
    </svg>
  ),
  sino: (p) => (
    <svg viewBox="0 0 24 24" width="20" height="20" {...p}>
      <path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15z M10 20a2 2 0 0 0 4 0" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinejoin="round" />
    </svg>
  ),
  pdf: (p) => (
    <svg viewBox="0 0 24 24" width="40" height="40" {...p}>
      <path d="M6 2.5h8l4.5 4.5v14.5H6z" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M14 2.5V7h4.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <text x="12" y="17" textAnchor="middle" fontSize="5.5" fontWeight="700" fill="currentColor">PDF</text>
    </svg>
  ),
  fechar: (p) => (
    <svg viewBox="0 0 24 24" width="14" height="14" {...p}>
      <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
    </svg>
  ),
  voltar: (p) => (
    <svg viewBox="0 0 24 24" width="16" height="16" {...p}>
      <path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  lixo: (p) => (
    <svg viewBox="0 0 24 24" width="16" height="16" {...p}>
      <path d="M5 7h14M10 7V4.5h4V7M7 7l1 13h8l1-13" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinejoin="round" />
    </svg>
  ),
}

// ------------------------------------------------------------------ estados
const ESTADOS = {
  // necessidade
  ABERTA: ['Aberta', 'verde'],
  RESOLVIDA: ['Resolvida', 'cinza'],
  // proposta técnica / marcenaria
  SUBMETIDA: ['Submetida', 'amarelo'],
  APROVADA: ['Aprovada', 'verde'],
  ARQUIVADA: ['Arquivada', 'cinza'],
  ACEITA: ['Aceita', 'verde'],
  RECUSADA: ['Recusada', 'cinza'],
  // ordem de serviço
  PENDENTE: ['Pendente', 'vermelho'],
  EM_USINAGEM: ['Iniciado · em usinagem', 'caramelo'],
  FINALIZADA: ['Finalizada', 'azul'],
  ENTREGA_ACORDADA: ['Entrega acordada', 'roxo'],
  ENTREGUE: ['Entregue', 'verde-escuro'],
  CANCELADA: ['Cancelada', 'vermelho'],
  // entrega
  AGUARDANDO: ['Aguardando avaliação', 'amarelo'],
  ALTERACAO_SOLICITADA: ['Alteração solicitada', 'cinza'],
  // pagamento
  APROVADO: ['Aprovado', 'verde'],
  RECUSADO: ['Recusado', 'vermelho'],
  REEMBOLSADO: ['Reembolsado', 'cinza'],
}

export function Estado({ valor, rotulo }) {
  if (!valor) return null
  const [texto, cor] = ESTADOS[valor] || [valor, 'cinza']
  return <span className={`estado estado-${cor}`}>{rotulo || texto}</span>
}

export function Contador({ n }) {
  if (!n) return null
  return <span className="contador">{n}</span>
}

// ------------------------------------------------------------------ toasts
const ToastContext = createContext(() => {})

export function ToastProvider({ children }) {
  const [itens, setItens] = useState([])
  const mostrar = useCallback((texto, tipo = 'ok') => {
    const id = Math.random().toString(36).slice(2)
    setItens((xs) => [...xs, { id, texto, tipo }])
    setTimeout(() => setItens((xs) => xs.filter((x) => x.id !== id)), 5000)
  }, [])
  return (
    <ToastContext.Provider value={mostrar}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {itens.map((t) => (
          <div key={t.id} className={`toast toast-${t.tipo}`}>
            {t.texto}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
export const useToast = () => useContext(ToastContext)

// ------------------------------------------------------------------ modal
export function Modal({ aberto, aoFechar, children, largura = 860, titulo }) {
  useEffect(() => {
    if (!aberto) return
    const esc = (e) => e.key === 'Escape' && aoFechar?.()
    document.addEventListener('keydown', esc)
    document.body.classList.add('sem-rolagem')
    return () => {
      document.removeEventListener('keydown', esc)
      document.body.classList.remove('sem-rolagem')
    }
  }, [aberto, aoFechar])
  if (!aberto) return null
  return (
    <div className="modal-fundo" onMouseDown={(e) => e.target === e.currentTarget && aoFechar?.()}>
      <div className="modal" style={{ maxWidth: largura }} role="dialog" aria-modal="true" aria-label={titulo}>
        {aoFechar && (
          <button className="botao-fechar" onClick={aoFechar} aria-label="Fechar">
            <Icone.fechar />
          </button>
        )}
        {children}
      </div>
    </div>
  )
}

// ------------------------------------------------------------------ imagens
export function PainelImagem({ src, rotulo, grande = false, onClick }) {
  const pdf = ehPdf(src)
  return (
    <div className={`painel-imagem ${grande ? 'grande' : ''} ${onClick ? 'clicavel' : ''}`} onClick={onClick}>
      {src && !pdf ? (
        <img src={src} alt={rotulo || ''} loading="lazy" />
      ) : (
        <div className="painel-vazio">
          {pdf ? <Icone.pdf /> : <Icone.imagem />}
          {rotulo && <span>{rotulo}</span>}
        </div>
      )}
    </div>
  )
}

export function Visualizador({ src, aoFechar }) {
  if (!src) return null
  return (
    <Modal aberto aoFechar={aoFechar} largura={1100} titulo="Visualizar arquivo">
      <div className="visualizador">
        {ehPdf(src) ? <iframe src={src} title="arquivo" /> : <img src={src} alt="" />}
        <a href={src} target="_blank" rel="noreferrer" className="link">
          Abrir em nova aba
        </a>
      </div>
    </Modal>
  )
}

export function MiniArquivo({ src, rotulo, aoAbrir }) {
  if (!src) return null
  return (
    <button type="button" className="mini-arquivo" onClick={() => aoAbrir(src)}>
      <span className="mini-thumb">{ehPdf(src) ? <Icone.pdf width="22" height="22" /> : <img src={src} alt="" />}</span>
      {rotulo}
    </button>
  )
}

// seletor de arquivo com pré-visualização (usado no painel esquerdo dos formulários)
export function SeletorArquivo({ arquivo, aoEscolher, rotulo, aceitar = 'image/png,image/jpeg', erro, grande = true }) {
  const input = useRef(null)
  const [preview, setPreview] = useState(null)
  useEffect(() => {
    if (!arquivo || arquivo.type === 'application/pdf') return setPreview(null)
    const url = URL.createObjectURL(arquivo)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [arquivo])
  return (
    <div className={`seletor-arquivo ${grande ? 'grande' : ''} ${erro ? 'com-erro' : ''}`} onClick={() => input.current?.click()}>
      <input
        ref={input}
        type="file"
        accept={aceitar}
        hidden
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => {
          aoEscolher(e.target.files[0] || null)
          e.target.value = ''
        }}
      />
      {preview ? (
        <img src={preview} alt="pré-visualização" />
      ) : (
        <div className="painel-vazio">
          {arquivo ? <Icone.pdf /> : <Icone.imagem />}
          <span>{arquivo ? arquivo.name : rotulo}</span>
        </div>
      )}
      {erro && <small className="erro-campo">{erro}</small>}
    </div>
  )
}

// ------------------------------------------------------------------ formulário
export function Campo({ rotulo, erro, children, dica, className = '', bloco = false }) {
  const Tag = bloco ? 'div' : 'label'
  return (
    <Tag className={`campo ${erro ? 'com-erro' : ''} ${className}`}>
      {rotulo && <span className="campo-rotulo">{rotulo}</span>}
      {children}
      {dica && !erro && <small className="dica">{dica}</small>}
      {erro && <small className="erro-campo">{erro}</small>}
    </Tag>
  )
}

export function Alerta({ tipo = 'erro', children }) {
  if (!children) return null
  return <div className={`alerta alerta-${tipo}`}>{children}</div>
}

// ------------------------------------------------------------------ layout
export function Carregando({ texto = 'Carregando…' }) {
  return (
    <div className="carregando">
      <span className="spinner" /> {texto}
    </div>
  )
}

export function Vazio({ titulo, children }) {
  return (
    <div className="vazio">
      <Icone.imagem width="36" height="36" />
      <strong>{titulo}</strong>
      {children && <p>{children}</p>}
    </div>
  )
}

export function Avatar({ nome, pequeno }) {
  const iniciais = (nome || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
  return <span className={`avatar ${pequeno ? 'pequeno' : ''}`}>{iniciais}</span>
}

// card no formato dos protótipos: imagem à esquerda, título e dados à direita
export function CardProjeto({ imagem, titulo, linhas = [], rodape, canto, contador, onClick, destaque }) {
  return (
    <div
      className={`card-projeto ${onClick ? 'clicavel' : ''} ${destaque ? 'destaque' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => onClick && e.key === 'Enter' && onClick()}
    >
      <Contador n={contador} />
      <PainelImagem src={imagem} />
      <div className="card-corpo">
        <div className="card-topo">
          <h3>{titulo}</h3>
          {canto}
        </div>
        {linhas.filter(Boolean).map((l, i) => (
          <p key={i} className="card-linha">
            {l}
          </p>
        ))}
        {rodape && <div className="card-rodape">{rodape}</div>}
      </div>
    </div>
  )
}

export function Voltar({ para, children = 'Voltar' }) {
  return (
    <a className="voltar" href={`#${para}`}>
      <Icone.voltar /> {children}
    </a>
  )
}

export function Etapas({ etapas, atual }) {
  const idx = etapas.findIndex((e) => e[0] === atual)
  return (
    <ol className="etapas">
      {etapas.map(([chave, rotulo], i) => (
        <li key={chave} className={i < idx ? 'feita' : i === idx ? 'atual' : ''}>
          <span className="etapa-bola">{i < idx ? '✓' : i + 1}</span>
          <span className="etapa-rotulo">{rotulo}</span>
        </li>
      ))}
    </ol>
  )
}

// usa a API e mantém estado de carregamento/erro
export function useCarregar(funcao, deps = []) {
  const [estado, setEstado] = useState({ dados: null, carregando: true, erro: null })
  const recarregar = useCallback(() => {
    setEstado((e) => ({ ...e, carregando: true, erro: null }))
    return funcao()
      .then((dados) => setEstado({ dados, carregando: false, erro: null }))
      .catch((erro) => setEstado({ dados: null, carregando: false, erro }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => {
    recarregar()
  }, [recarregar])
  return { ...estado, recarregar }
}

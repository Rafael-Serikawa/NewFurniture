import { useEffect } from 'react'
import { rotaInicial, useAuth } from './auth'
import Navbar from './components/Navbar'
import { Carregando } from './components/ui'
import { casar, navegar, useRota } from './router'
import Cadastro from './pages/Cadastro'
import Login from './pages/Login'
import Sobre from './pages/Sobre'

// [padrão, componente, perfis permitidos (vazio = qualquer usuário logado)]
const ROTAS = [
]

function Redirecionar({ para }) {
  useEffect(() => navegar(para), [para])
  return null
}

function Conteudo({ caminho }) {
  const { usuario } = useAuth()

  if (caminho === '/sobre') return <Sobre />
  if (caminho === '/login' || caminho === '/cadastro') {
    if (usuario) return <Redirecionar para={rotaInicial(usuario)} />
    return caminho === '/login' ? <Login /> : <Cadastro />
  }
  if (!usuario) return <Redirecionar para="/login" />
  if (caminho === '/') return <Redirecionar para={rotaInicial(usuario)} />

  for (const [padrao, Pagina, perfis] of ROTAS) {
    const params = casar(padrao, caminho)
    if (!params) continue
    if (perfis.length && !perfis.includes(usuario.tipo)) return <Redirecionar para={rotaInicial(usuario)} />
    return <Pagina key={caminho} {...params} />
  }
  return (
    <div className="pagina">
      <h1>Página não encontrada</h1>
      <a href={`#${rotaInicial(usuario)}`}>Voltar ao início</a>
    </div>
  )
}

export default function App() {
  const caminho = useRota()
  const { usuario, carregando } = useAuth()
  const telaCheia = !usuario && (caminho === '/login' || caminho === '/cadastro')

  if (carregando) return <Carregando texto="Conectando…" />
  return (
    <>
      {!telaCheia && <Navbar caminho={caminho} />}
      <main className={telaCheia ? '' : 'conteudo'}>
        <Conteudo caminho={caminho} />
      </main>
      {!telaCheia && (
        <footer className="rodape">
          NewFurniture · PMR3304 Sistemas de Informação · Poli-USP 2026
        </footer>
      )}
    </>
  )
}

import { useState } from 'react'
import { rotaInicial, useAuth } from '../auth'
import { Logo } from '../components/Navbar'
import { Alerta, Campo } from '../components/ui'
import { Link, navegar } from '../router'

const DEMOS = [
  ['Cliente', 'ana@cliente.com'],
  ['Designer', 'carla@designer.com'],
  ['Marceneiro', 'eduardo@marceneiro.com'],
]

export function Fluxo() {
  return (
    <ol className="fluxo">
      <li>
        <b>1</b>
        <div>
          <strong>Cliente</strong> cadastra a necessidade e as medidas do ambiente
        </div>
      </li>
      <li>
        <b>2</b>
        <div>
          <strong>Designers</strong> enviam propostas de desenho técnico
        </div>
      </li>
      <li>
        <b>3</b>
        <div>
          <strong>Marceneiro</strong> fabrica as peças para automontagem
        </div>
      </li>
    </ol>
  )
}

export default function Login() {
  const { entrar } = useAuth()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const fazerLogin = async (e, credenciais) => {
    e?.preventDefault()
    setEnviando(true)
    setErro('')
    try {
      const u = await entrar(...(credenciais || [email, senha]))
      navegar(rotaInicial(u))
    } catch (err) {
      setErro(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="tela-auth">
      <aside className="auth-marca">
        <Logo />
        <h1>Móveis sob medida, sem intermediários.</h1>
        <p>Uma plataforma que conecta quem precisa de um móvel, quem desenha e quem fabrica.</p>
        <Fluxo />
      </aside>
      <main className="auth-form">
        <form onSubmit={fazerLogin} className="cartao-auth">
          <h2>Entrar</h2>
          <p className="subtitulo">Acesse sua conta NewFurniture</p>
          <Alerta>{erro}</Alerta>
          <Campo rotulo="E-mail">
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required autoFocus />
          </Campo>
          <Campo rotulo="Senha">
            <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} autoComplete="current-password" required />
          </Campo>
          <button className="botao botao-bloco" disabled={enviando}>
            {enviando ? 'Entrando…' : 'Entrar'}
          </button>
          <p className="centro">
            Ainda não tem conta? <Link para="/cadastro">Cadastre-se</Link>
          </p>
          <div className="demo">
            <span>Contas de demonstração (senha: senha123)</span>
            <div>
              {DEMOS.map(([papel, mail]) => (
                <button key={mail} type="button" className="botao botao-contorno botao-pequeno" disabled={enviando} onClick={(e) => fazerLogin(e, [mail, 'senha123'])}>
                  {papel}
                </button>
              ))}
            </div>
          </div>
        </form>
      </main>
    </div>
  )
}

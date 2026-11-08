import { useState } from 'react'
import { rotaInicial, useAuth } from '../auth'
import { Logo } from '../components/Navbar'
import { Alerta, Campo } from '../components/ui'
import { Link, navegar } from '../router'
import { Fluxo } from './Login'

const PERFIS = [
  ['CLIENTE', 'Cliente', 'Quero um móvel sob medida mais barato e monto em casa.'],
  ['DESIGNER', 'Designer / Arquiteto', 'Desenho móveis funcionais e quero uma renda extra.'],
  ['MARCENEIRO', 'Marceneiro', 'Tenho marcenaria e quero fabricar projetos prontos.'],
]

export default function Cadastro() {
  const { cadastrar } = useAuth()
  const [form, setForm] = useState({ nome: '', email: '', senha: '', confirmar: '', tipo: 'CLIENTE', cidade: '' })
  const [erros, setErros] = useState({})
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const mudar = (c) => (e) => setForm((f) => ({ ...f, [c]: e.target.value }))

  const enviar = async (e) => {
    e.preventDefault()
    setErros({})
    setErro('')
    if (form.senha !== form.confirmar) return setErros({ confirmar: 'As senhas não conferem.' })
    setEnviando(true)
    try {
      const { confirmar, ...dados } = form
      const u = await cadastrar(dados)
      navegar(rotaInicial(u))
    } catch (err) {
      setErro(err.message)
      setErros(err.campos || {})
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="tela-auth">
      <aside className="auth-marca">
        <Logo />
        <h1>Crie sua conta.</h1>
        <p>Escolha o seu perfil: cada um tem acesso às funções certas na plataforma.</p>
        <Fluxo />
      </aside>
      <main className="auth-form">
        <form onSubmit={enviar} className="cartao-auth largo">
          <h2>Cadastro</h2>
          <Alerta>{erro}</Alerta>
          <div className="perfis">
            {PERFIS.map(([valor, rotulo, desc]) => (
              <label key={valor} className={`perfil-opcao ${form.tipo === valor ? 'selecionado' : ''}`}>
                <input type="radio" name="tipo" value={valor} checked={form.tipo === valor} onChange={mudar('tipo')} />
                <strong>{rotulo}</strong>
                <small>{desc}</small>
              </label>
            ))}
          </div>
          <Campo rotulo="Nome completo" erro={erros.nome}>
            <input value={form.nome} onChange={mudar('nome')} required maxLength={150} />
          </Campo>
          <div className="linha-campos">
            <Campo rotulo="E-mail" erro={erros.email}>
              <input type="email" value={form.email} onChange={mudar('email')} required />
            </Campo>
            <Campo rotulo="Cidade" erro={erros.cidade}>
              <input value={form.cidade} onChange={mudar('cidade')} maxLength={100} />
            </Campo>
          </div>
          <div className="linha-campos">
            <Campo rotulo="Senha" erro={erros.senha} dica="Mínimo de 6 caracteres">
              <input type="password" value={form.senha} onChange={mudar('senha')} minLength={6} required />
            </Campo>
            <Campo rotulo="Confirmar senha" erro={erros.confirmar}>
              <input type="password" value={form.confirmar} onChange={mudar('confirmar')} required />
            </Campo>
          </div>
          <button className="botao botao-bloco" disabled={enviando}>
            {enviando ? 'Criando conta…' : 'Criar conta'}
          </button>
          <p className="centro">
            Já tem conta? <Link para="/login">Entrar</Link>
          </p>
        </form>
      </main>
    </div>
  )
}

import { useState } from 'react'
import { moeda } from '../api'
import { Alerta, Campo, Modal } from './ui'

// Interface de checkout (APR001 passos 4-6). O pagamento é simulado no backend:
// cartões terminados em 0000 são recusados pela "operadora".
export default function Checkout({ aberto, titulo, itens, total, observacao, aoFechar, aoPagar }) {
  const [form, setForm] = useState({ nome_titular: '', numero_cartao: '', validade: '', cvv: '' })
  const [erros, setErros] = useState({})
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const mudar = (campo) => (e) => {
    let v = e.target.value
    if (campo === 'numero_cartao') v = v.replace(/\D/g, '').slice(0, 19).replace(/(\d{4})(?=\d)/g, '$1 ')
    if (campo === 'validade') v = v.replace(/\D/g, '').slice(0, 4).replace(/^(\d{2})(\d)/, '$1/$2')
    if (campo === 'cvv') v = v.replace(/\D/g, '').slice(0, 4)
    setForm((f) => ({ ...f, [campo]: v }))
  }

  const enviar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    setErro('')
    setErros({})
    try {
      await aoPagar(form)
    } catch (err) {
      setErro(err.message)
      setErros(err.campos || {})
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal aberto={aberto} aoFechar={enviando ? undefined : aoFechar} largura={760} titulo={titulo}>
      <div className="checkout">
        <div className="checkout-resumo">
          <h2>{titulo}</h2>
          <table className="tabela-resumo">
            <tbody>
              {itens.map(([rotulo, valor]) => (
                <tr key={rotulo}>
                  <td>{rotulo}</td>
                  <td>{moeda(valor)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td>Total a pagar agora</td>
                <td>{moeda(total)}</td>
              </tr>
            </tfoot>
          </table>
          {observacao && <p className="nota">{observacao}</p>}
        </div>
        <form className="checkout-form" onSubmit={enviar}>
          <h3>Dados do pagamento</h3>
          <Alerta>{erro}</Alerta>
          <Campo rotulo="Nome impresso no cartão" erro={erros.nome_titular}>
            <input value={form.nome_titular} onChange={mudar('nome_titular')} autoComplete="cc-name" required />
          </Campo>
          <Campo rotulo="Número do cartão" erro={erros.numero_cartao}>
            <input value={form.numero_cartao} onChange={mudar('numero_cartao')} inputMode="numeric" placeholder="0000 0000 0000 0000" autoComplete="cc-number" required />
          </Campo>
          <div className="linha-campos">
            <Campo rotulo="Validade" erro={erros.validade}>
              <input value={form.validade} onChange={mudar('validade')} placeholder="MM/AA" autoComplete="cc-exp" required />
            </Campo>
            <Campo rotulo="CVV" erro={erros.cvv}>
              <input value={form.cvv} onChange={mudar('cvv')} inputMode="numeric" placeholder="123" autoComplete="cc-csc" required />
            </Campo>
          </div>
          <p className="nota">
            Pagamento simulado para fins acadêmicos. Cartões terminados em <b>0000</b> são recusados.
          </p>
          <div className="acoes">
            <button type="button" className="botao botao-texto" onClick={aoFechar} disabled={enviando}>
              Cancelar
            </button>
            <button className="botao" disabled={enviando}>
              {enviando ? 'Processando…' : `Confirmar ${moeda(total)}`}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  )
}

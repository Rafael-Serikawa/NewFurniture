import { useState } from 'react'
import { api, moeda } from '../api'
import Checkout from '../components/Checkout'
import { CardPropostaTecnica, PainelNecessidade } from '../components/Propostas'
import { Alerta, Carregando, Estado, Vazio, Visualizador, Voltar, useCarregar, useToast } from '../components/ui'
import { Link, navegar } from '../router'

// APR001 - Aprovar proposta de móvel (visão do cliente)
export default function PedidoDetalhe({ id }) {
  const toast = useToast()
  const [arquivo, setArquivo] = useState(null)
  const [escolhida, setEscolhida] = useState(null)
  const { dados: n, carregando, erro } = useCarregar(() => api(`/necessidades/${id}/`), [id])

  if (carregando && !n) return <Carregando />
  if (erro) return <div className="pagina"><Alerta>{erro.message}</Alerta></div>

  const pagar = async (cartao) => {
    const r = await api(`/propostas-tecnicas/${escolhida.id}/aprovar/`, { method: 'POST', body: cartao })
    setEscolhida(null)
    toast('Pagamento aprovado! A ordem de serviço foi enviada às marcenarias.')
    window.dispatchEvent(new Event('nf:atualizar-notificacoes'))
    navegar(`/ordens/${r.ordem_id}`)
  }

  const submetidas = n.propostas.filter((p) => p.estado === 'SUBMETIDA')
  const ordenadas = [...n.propostas].sort((a, b) => (a.estado === 'SUBMETIDA' ? -1 : 1) - (b.estado === 'SUBMETIDA' ? -1 : 1))

  return (
    <div className="pagina">
      <Voltar para="/pedidos">Meus pedidos</Voltar>
      <PainelNecessidade n={n} aoVerArquivo={setArquivo} extra={<Estado valor={n.estado} />} />

      {n.ordem_id && (
        <Alerta tipo="info">
          Necessidade resolvida. <Link para={`/ordens/${n.ordem_id}`}>Acompanhar a ordem de serviço →</Link>
        </Alerta>
      )}

      <div className="secao-titulo">
        <h2>Propostas</h2>
        {n.estado === 'ABERTA' && <span className="texto-suave">{submetidas.length} aguardando sua decisão</span>}
      </div>

      {n.propostas.length === 0 ? (
        <Vazio titulo="Nenhuma proposta ainda">Sua necessidade está visível para a rede de designers. Você será notificado.</Vazio>
      ) : (
        <div className="lista-propostas">
          {ordenadas.map((p) => (
            <CardPropostaTecnica
              key={p.id}
              proposta={p}
              aoVerArquivo={setArquivo}
              acao={
                n.estado === 'ABERTA' && p.estado === 'SUBMETIDA' ? (
                  <button className="botao" onClick={() => setEscolhida(p)}>
                    Aprovar e pagar {moeda(p.valor_projeto)}
                  </button>
                ) : null
              }
            />
          ))}
        </div>
      )}

      {escolhida && (
        <Checkout
          aberto
          titulo={`Aprovar proposta de ${escolhida.designer_nome}`}
          itens={[
            ['Materiais', escolhida.custo_materiais],
            ['Comissão do designer', escolhida.comissao_designer],
          ]}
          total={escolhida.valor_projeto}
          observacao={`A mão de obra (estimada em ${moeda(escolhida.estimativa_mao_obra)}) será paga depois, ao marceneiro que você escolher. As demais propostas serão arquivadas.`}
          aoFechar={() => setEscolhida(null)}
          aoPagar={pagar}
        />
      )}
      <Visualizador src={arquivo} aoFechar={() => setArquivo(null)} />
    </div>
  )
}

import { api, medidas, moeda } from '../api'
import { Alerta, Avatar, CardProjeto, Carregando, Estado, Vazio, useCarregar } from '../components/ui'
import { navegar } from '../router'

function CardOrdem({ o, rodape }) {
  return (
    <CardProjeto
      imagem={o.necessidade.foto_ambiente}
      titulo={o.necessidade.titulo}
      canto={<Avatar nome={o.necessidade.cliente_nome} pequeno />}
      linhas={[`${o.necessidade.tipo_ambiente_display} · ${o.necessidade.cidade}`, medidas(o.necessidade)]}
      rodape={rodape}
      onClick={() => navegar(`/ordens/${o.id}`)}
    />
  )
}

// Ordens de serviço "Pendentes" ainda sem marceneiro: marcenarias concorrem pela execução
export function OrdensDisponiveis() {
  const { dados, carregando, erro } = useCarregar(() => api('/ordens/?escopo=disponiveis'))
  return (
    <div className="pagina">
      <div className="pagina-topo">
        <div>
          <h1>Projetos disponíveis</h1>
          <p className="texto-suave">Projetos técnicos aprovados e pagos, aguardando uma marcenaria. Envie sua proposta de execução.</p>
        </div>
      </div>
      {erro && <Alerta>{erro.message}</Alerta>}
      {carregando && !dados ? (
        <Carregando />
      ) : !(dados || []).length ? (
        <Vazio titulo="Nenhuma ordem de serviço disponível">Você será notificado quando um cliente aprovar um novo projeto.</Vazio>
      ) : (
        <div className="grade-cards">
          {(dados || []).map((o) => (
            <CardOrdem
              key={o.id}
              o={o}
              rodape={
                <>
                  {o.minha_proposta_status ? (
                    <span className="estado estado-amarelo">Proposta enviada</span>
                  ) : (
                    <Estado valor="PENDENTE" />
                  )}
                  <span className="texto-suave"> {o.total_propostas_marcenaria} proposta(s)</span>
                </>
              }
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Ordens sob responsabilidade do marceneiro (MAR001, MAR002, ENT001)
export function MeusProjetos() {
  const { dados, carregando, erro } = useCarregar(() => api('/ordens/?escopo=meus'))
  return (
    <div className="pagina">
      <div className="pagina-topo">
        <h1>Meus projetos</h1>
      </div>
      {erro && <Alerta>{erro.message}</Alerta>}
      {carregando && !dados ? (
        <Carregando />
      ) : !(dados || []).length ? (
        <Vazio titulo="Nenhum projeto em andamento">Envie propostas de execução em "Projetos disponíveis".</Vazio>
      ) : (
        <div className="grade-cards">
          {(dados || []).map((o) => (
            <CardOrdem
              key={o.id}
              o={o}
              rodape={
                o.estado === 'FINALIZADA' && !o.entrega_aguardando ? (
                  <button
                    className="botao botao-pequeno"
                    onClick={(e) => {
                      e.stopPropagation()
                      navegar(`/ordens/${o.id}`)
                    }}
                  >
                    Adicionar método de entrega
                  </button>
                ) : (
                  <>
                    <Estado valor={o.estado} />
                    {o.entrega_aguardando && <span className="texto-suave"> entrega em avaliação</span>}
                    <span className="texto-suave">{moeda(o.preco_total)}</span>
                  </>
                )
              }
            />
          ))}
        </div>
      )}
    </div>
  )
}

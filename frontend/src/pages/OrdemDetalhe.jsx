import { useState } from 'react'
import { api, dataCurta, dataHora, moeda, numero } from '../api'
import { useAuth } from '../auth'
import Checkout from '../components/Checkout'
import { CardPropostaTecnica, PainelNecessidade } from '../components/Propostas'
import { Alerta, Avatar, Campo, Carregando, Estado, Etapas, Modal, Visualizador, Voltar, useCarregar, useToast } from '../components/ui'
import { Link } from '../router'

const ETAPAS = [
  ['ESCOLHA', 'Escolha do marceneiro'],
  ['PENDENTE', 'Aguardando início'],
  ['EM_USINAGEM', 'Em usinagem'],
  ['FINALIZADA', 'Finalizada'],
  ['ENTREGA_ACORDADA', 'Entrega acordada'],
  ['ENTREGUE', 'Entregue'],
]

const VOLTAR = {
  CLIENTE: ['/pedidos', 'Meus pedidos'],
  DESIGNER: ['/minhas-propostas', 'Minhas propostas'],
  MARCENEIRO: ['/meus-projetos', 'Meus projetos'],
}

// ---------------------------------------------------------------- marceneiro
function FormPropostaExecucao({ ordem, usuario, aoAgir }) {
  const [form, setForm] = useState({
    horas_trabalho: ordem.proposta_tecnica.horas_estimadas || '',
    valor_hora: usuario.valor_hora || 60,
    prazo_estimado_dias: '',
    descricao: '',
  })
  const [erros, setErros] = useState({})
  const mudar = (c) => (e) => setForm((f) => ({ ...f, [c]: e.target.value }))
  const custo = (Number(form.horas_trabalho) || 0) * (Number(form.valor_hora) || 0)
  const enviar = (e) => {
    e.preventDefault()
    setErros({})
    aoAgir('propor-execucao', form, 'Proposta de execução enviada ao cliente!').then((r) => !r.ok && setErros(r.erro.campos || {}))
  }
  return (
    <form onSubmit={enviar} className="painel-acao">
      <h3>Enviar proposta de execução</h3>
      <p className="texto-suave">Informe as horas de trabalho, o seu valor-hora e o prazo. O cliente escolherá entre as marcenarias.</p>
      <div className="linha-campos tres">
        <Campo rotulo="Horas de trabalho" erro={erros.horas_trabalho}>
          <input type="number" min="0.5" step="0.5" required value={form.horas_trabalho} onChange={mudar('horas_trabalho')} />
        </Campo>
        <Campo rotulo="Valor da hora (R$)" erro={erros.valor_hora}>
          <input type="number" min="1" step="0.01" required value={form.valor_hora} onChange={mudar('valor_hora')} />
        </Campo>
        <Campo rotulo="Prazo (dias)" erro={erros.prazo_estimado_dias}>
          <input type="number" min="1" step="1" required value={form.prazo_estimado_dias} onChange={mudar('prazo_estimado_dias')} />
        </Campo>
      </div>
      <Campo rotulo="Observações (opcional)" erro={erros.descricao}>
        <textarea rows="2" maxLength={700} value={form.descricao} onChange={mudar('descricao')} />
      </Campo>
      <div className="acoes">
        <span className="valor-destaque">Custo da execução: {moeda(custo)}</span>
        <button className="botao">Enviar proposta</button>
      </div>
    </form>
  )
}

function FormEntrega({ ordem, aoAgir }) {
  const ultima = ordem.propostas_entrega[ordem.propostas_entrega.length - 1]
  const [form, setForm] = useState({
    modalidade: ultima?.modalidade || 'DELIVERY',
    local: ultima?.local || '',
    prazo: '',
    horarios_disponiveis: '',
    instrucoes: '',
  })
  const [erros, setErros] = useState({})
  const [aberto, setAberto] = useState(false)
  const mudar = (c) => (e) => setForm((f) => ({ ...f, [c]: e.target.value }))
  const enviar = (e) => {
    e.preventDefault()
    setErros({})
    aoAgir('propor-entrega', form, 'Proposta de entrega enviada ao cliente!').then((r) =>
      r.ok ? setAberto(false) : setErros(r.erro.campos || {}),
    )
  }
  if (!aberto)
    return (
      <div className="painel-acao">
        <h3>Fabricação finalizada</h3>
        {ultima?.estado === 'ALTERACAO_SOLICITADA' && (
          <Alerta tipo="aviso">
            O cliente pediu alteração: “{ultima.justificativa_cliente}”. Envie uma nova proposta.
          </Alerta>
        )}
        <p className="texto-suave">Proponha ao cliente como as peças serão entregues ou retiradas.</p>
        <button className="botao" onClick={() => setAberto(true)}>
          Propor método de entrega
        </button>
      </div>
    )
  return (
    <form onSubmit={enviar} className="painel-acao">
      <h3>Propor método de entrega</h3>
      <div className="opcoes-modalidade">
        {[
          ['DELIVERY', 'Delivery', 'Entrega no endereço do cliente'],
          ['RETIRADA', 'Retirada', 'Cliente retira na marcenaria'],
        ].map(([v, r, d]) => (
          <label key={v} className={`perfil-opcao ${form.modalidade === v ? 'selecionado' : ''}`}>
            <input type="radio" name="modalidade" value={v} checked={form.modalidade === v} onChange={mudar('modalidade')} />
            <strong>{r}</strong>
            <small>{d}</small>
          </label>
        ))}
      </div>
      <Campo rotulo={form.modalidade === 'DELIVERY' ? 'Endereço de entrega' : 'Endereço para retirada'} erro={erros.local}>
        <input required maxLength={200} value={form.local} onChange={mudar('local')} />
      </Campo>
      <div className="linha-campos">
        <Campo rotulo="Data prevista" erro={erros.prazo}>
          <input type="date" required value={form.prazo} onChange={mudar('prazo')} />
        </Campo>
        <Campo rotulo="Horários disponíveis" erro={erros.horarios_disponiveis}>
          <input required maxLength={200} placeholder="Ex.: Seg a sex, 14h às 18h" value={form.horarios_disponiveis} onChange={mudar('horarios_disponiveis')} />
        </Campo>
      </div>
      <Campo rotulo="Instruções adicionais" erro={erros.instrucoes}>
        <textarea rows="2" maxLength={700} value={form.instrucoes} onChange={mudar('instrucoes')} />
      </Campo>
      <div className="acoes">
        <button type="button" className="botao botao-texto" onClick={() => setAberto(false)}>
          Cancelar
        </button>
        <button className="botao">Enviar proposta</button>
      </div>
    </form>
  )
}

function AcoesMarceneiro({ ordem, usuario, aoAgir }) {
  const [recusando, setRecusando] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [finalizando, setFinalizando] = useState(false)
  const responsavel = ordem.marceneiro_id === usuario.id
  const minha = ordem.propostas_marcenaria[0]

  if (ordem.estado === 'PENDENTE' && !ordem.marceneiro_id) {
    if (minha)
      return (
        <div className="painel-acao">
          <h3>Sua proposta de execução</h3>
          <p>
            {numero(minha.horas_trabalho)} h × {moeda(minha.valor_hora)} = <b>{moeda(minha.custo_execucao)}</b> · prazo de{' '}
            {minha.prazo_estimado_dias} dias
          </p>
          <Estado valor={minha.status} rotulo={minha.status === 'SUBMETIDA' ? 'Aguardando escolha do cliente' : undefined} />
        </div>
      )
    return <FormPropostaExecucao ordem={ordem} usuario={usuario} aoAgir={aoAgir} />
  }
  if (!responsavel) {
    return (
      <Alerta tipo="info">
        {minha?.status === 'RECUSADA' ? 'O cliente escolheu outra marcenaria para este projeto.' : 'Esta ordem está com outro marceneiro.'}
      </Alerta>
    )
  }
  if (ordem.estado === 'PENDENTE')
    return (
      <div className="painel-acao">
        <h3>Você foi escolhido para fabricar este móvel</h3>
        <p className="texto-suave">Confira o desenho técnico e os materiais abaixo antes de iniciar.</p>
        {!recusando ? (
          <div className="acoes esquerda">
            <button className="botao" onClick={() => aoAgir('iniciar-usinagem', {}, 'Produção iniciada! Ordem em usinagem.')}>
              Iniciar usinagem
            </button>
            <button className="botao botao-texto perigo" onClick={() => setRecusando(true)}>
              Recusar ordem
            </button>
          </div>
        ) : (
          <div className="recusa">
            <Campo rotulo="Motivo da recusa">
              <textarea rows="3" autoFocus value={motivo} onChange={(e) => setMotivo(e.target.value)} placeholder="Ex.: não tenho maquinário para esse tipo de corte" />
            </Campo>
            <div className="acoes esquerda">
              <button className="botao botao-perigo" disabled={!motivo.trim()} onClick={() => aoAgir('recusar', { motivo }, 'Ordem recusada. O cliente foi reembolsado.')}>
                Confirmar recusa
              </button>
              <button className="botao botao-texto" onClick={() => setRecusando(false)}>
                Voltar
              </button>
            </div>
          </div>
        )}
      </div>
    )
  if (ordem.estado === 'EM_USINAGEM')
    return (
      <div className="painel-acao">
        <h3>Em usinagem desde {dataCurta(ordem.data_inicio)}</h3>
        <p className="texto-suave">Quando as peças estiverem cortadas, furadas, com acabamento e embaladas, finalize a fabricação.</p>
        <button className="botao" onClick={() => setFinalizando(true)}>
          Finalizar fabricação
        </button>
        <Modal aberto={finalizando} aoFechar={() => setFinalizando(false)} largura={520} titulo="Finalizar fabricação">
          <div className="modal-simples">
            <h2>Finalizar fabricação?</h2>
            <p>
              <b>{ordem.necessidade.titulo}</b> — o cliente será avisado de que o kit está pronto para a etapa de logística.
            </p>
            <div className="acoes">
              <button className="botao botao-texto" onClick={() => setFinalizando(false)}>
                Cancelar
              </button>
              <button
                className="botao"
                onClick={() => aoAgir('finalizar', {}, 'Fabricação finalizada! Agora proponha o método de entrega.').then(() => setFinalizando(false))}
              >
                Projeto finalizado
              </button>
            </div>
          </div>
        </Modal>
      </div>
    )
  if (ordem.estado === 'FINALIZADA')
    return ordem.entrega_aguardando ? (
      <Alerta tipo="info">Proposta de entrega enviada. Aguardando a avaliação do cliente.</Alerta>
    ) : (
      <FormEntrega ordem={ordem} aoAgir={aoAgir} />
    )
  if (ordem.estado === 'ENTREGA_ACORDADA') return <Alerta tipo="ok">Entrega acordada com o cliente. Despache ou aguarde a retirada das peças.</Alerta>
  if (ordem.estado === 'CANCELADA') return <Alerta tipo="info">Você recusou esta ordem: “{ordem.motivo_recusa}”.</Alerta>
  return null
}

// ---------------------------------------------------------------- cliente
function AcoesCliente({ ordem, aoAgir, aoEscolher }) {
  const [alterando, setAlterando] = useState(false)
  const [justificativa, setJustificativa] = useState('')
  const aguardando = ordem.propostas_entrega.find((p) => p.estado === 'AGUARDANDO')

  if (ordem.estado === 'PENDENTE' && !ordem.marceneiro_id) {
    const abertas = ordem.propostas_marcenaria.filter((p) => p.status === 'SUBMETIDA')
    return (
      <div className="painel-acao">
        <h3>Escolha a marcenaria</h3>
        {abertas.length === 0 ? (
          <p className="texto-suave">Seu projeto foi enviado às marcenarias. Aguarde as propostas de execução — você será notificado.</p>
        ) : (
          <div className="lista-marceneiros">
            {abertas.map((p) => (
              <div key={p.id} className="opcao-marceneiro">
                <Avatar nome={p.marceneiro_nome} pequeno />
                <div>
                  <strong>{p.marceneiro_nome}</strong>
                  <small>
                    {p.marceneiro_cidade} · {numero(p.horas_trabalho)} h × {moeda(p.valor_hora)} · prazo {p.prazo_estimado_dias} dias
                  </small>
                  {p.descricao && <small className="descricao">{p.descricao}</small>}
                </div>
                <button className="botao" onClick={() => aoEscolher(p)}>
                  Escolher e pagar {moeda(p.custo_execucao)}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }
  if (ordem.estado === 'PENDENTE') return <Alerta tipo="info">Aguardando {ordem.marceneiro_nome} iniciar a usinagem.</Alerta>
  if (ordem.estado === 'EM_USINAGEM') return <Alerta tipo="info">{ordem.marceneiro_nome} está fabricando as peças.</Alerta>
  if (ordem.estado === 'CANCELADA')
    return (
      <div className="painel-acao alerta-borda">
        <h3>O marceneiro recusou esta ordem</h3>
        <p>Motivo: “{ordem.motivo_recusa}”. O pagamento da execução foi reembolsado e o seu projeto técnico foi mantido.</p>
        <button className="botao" onClick={() => aoAgir('redirecionar', {}, 'Ordem reenviada para outras marcenarias.')}>
          Redirecionar para outra marcenaria
        </button>
      </div>
    )
  if (ordem.estado === 'FINALIZADA') {
    if (!aguardando) return <Alerta tipo="info">Peças prontas! Aguardando o marceneiro propor o método de entrega.</Alerta>
    return (
      <div className="painel-acao">
        <h3>Avaliar método de entrega</h3>
        <DetalheEntrega p={aguardando} />
        {!alterando ? (
          <div className="acoes esquerda">
            <button className="botao" onClick={() => aoAgir('avaliar-entrega', { acao: 'aprovar' }, 'Entrega acordada! O marceneiro foi notificado.')}>
              Aprovar proposta
            </button>
            <button className="botao botao-contorno" onClick={() => setAlterando(true)}>
              Solicitar alteração
            </button>
          </div>
        ) : (
          <div>
            <Campo rotulo="Justificativa ou contraproposta">
              <textarea rows="3" autoFocus maxLength={700} value={justificativa} onChange={(e) => setJustificativa(e.target.value)} />
            </Campo>
            <div className="acoes esquerda">
              <button
                className="botao"
                disabled={!justificativa.trim()}
                onClick={() => aoAgir('avaliar-entrega', { acao: 'alterar', justificativa }, 'Pedido de alteração enviado ao marceneiro.').then((r) => r.ok && setAlterando(false))}
              >
                Enviar
              </button>
              <button className="botao botao-texto" onClick={() => setAlterando(false)}>
                Cancelar
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }
  if (ordem.estado === 'ENTREGA_ACORDADA')
    return (
      <div className="painel-acao">
        <h3>Entrega acordada</h3>
        <p className="texto-suave">Quando receber as peças, confirme o recebimento para concluir o projeto e partir para a automontagem.</p>
        <button className="botao" onClick={() => aoAgir('confirmar-recebimento', {}, 'Projeto concluído! Bom proveito do seu móvel.')}>
          Confirmar recebimento
        </button>
      </div>
    )
  return null
}

function DetalheEntrega({ p }) {
  return (
    <dl className="detalhe-entrega">
      <dt>Modalidade</dt>
      <dd>{p.modalidade_display}</dd>
      <dt>Local</dt>
      <dd>{p.local}</dd>
      <dt>Data prevista</dt>
      <dd>{dataCurta(p.prazo)}</dd>
      <dt>Horários</dt>
      <dd>{p.horarios_disponiveis}</dd>
      {p.instrucoes && (
        <>
          <dt>Instruções</dt>
          <dd>{p.instrucoes}</dd>
        </>
      )}
    </dl>
  )
}

// ---------------------------------------------------------------- página
export default function OrdemDetalhe({ id }) {
  const { usuario } = useAuth()
  const toast = useToast()
  const [arquivo, setArquivo] = useState(null)
  const [escolhida, setEscolhida] = useState(null)
  const [erroAcao, setErroAcao] = useState('')
  const { dados: ordem, carregando, erro, recarregar } = useCarregar(() => api(`/ordens/${id}/`), [id])

  if (carregando && !ordem) return <Carregando />
  if (erro) return <div className="pagina"><Alerta>{erro.message}</Alerta></div>

  // executa uma ação da OS; devolve { ok } (nunca rejeita) para os formulários tratarem erros por campo
  const aoAgir = async (acao, body, mensagem) => {
    setErroAcao('')
    try {
      await api(`/ordens/${ordem.id}/${acao}/`, { method: 'POST', body })
      toast(mensagem)
      window.dispatchEvent(new Event('nf:atualizar-notificacoes'))
      await recarregar()
      return { ok: true }
    } catch (erro) {
      setErroAcao(erro.message)
      return { ok: false, erro }
    }
  }

  const pagarMarceneiro = async (cartao) => {
    await api(`/ordens/${ordem.id}/escolher-marceneiro/`, {
      method: 'POST',
      body: { ...cartao, proposta_marcenaria: escolhida.id },
    })
    setEscolhida(null)
    toast(`${escolhida.marceneiro_nome} vai fabricar o seu móvel!`)
    recarregar()
  }

  const n = ordem.necessidade
  const etapa = ordem.estado === 'PENDENTE' && !ordem.marceneiro_id ? 'ESCOLHA' : ordem.estado
  const orc = ordem.orcamento
  const [rotaVoltar, rotuloVoltar] =
    usuario.tipo === 'MARCENEIRO' && !ordem.marceneiro_id ? ['/ordens-disponiveis', 'Projetos disponíveis'] : VOLTAR[usuario.tipo]

  return (
    <div className="pagina">
      <Voltar para={rotaVoltar}>{rotuloVoltar}</Voltar>
      <PainelNecessidade
        n={n}
        aoVerArquivo={setArquivo}
        extra={
          <>
            <span className="codigo">OS #{ordem.id}</span>
            <Estado valor={ordem.estado} />
          </>
        }
      />

      {ordem.estado === 'CANCELADA' ? (
        <Alerta>Ordem cancelada pelo marceneiro.</Alerta>
      ) : (
        <Etapas etapas={ETAPAS} atual={etapa} />
      )}

      <div className="ordem-grade">
        <div className="ordem-principal">
          <Alerta>{erroAcao}</Alerta>
          {usuario.tipo === 'MARCENEIRO' && <AcoesMarceneiro ordem={ordem} usuario={usuario} aoAgir={aoAgir} />}
          {usuario.tipo === 'CLIENTE' && <AcoesCliente ordem={ordem} aoAgir={aoAgir} aoEscolher={setEscolhida} />}
          {usuario.tipo === 'DESIGNER' && (
            <Alerta tipo="info">
              Sua proposta foi aprovada.{' '}
              {ordem.marceneiro_nome ? `Fabricação com ${ordem.marceneiro_nome}.` : 'Aguardando a escolha da marcenaria.'}
            </Alerta>
          )}

          <h2 className="secao-h">Projeto técnico aprovado</h2>
          <CardPropostaTecnica proposta={ordem.proposta_tecnica} aoVerArquivo={setArquivo} mostrarEstado={false} />

          {ordem.propostas_entrega.length > 0 && (
            <>
              <h2 className="secao-h">Logística — histórico de propostas</h2>
              <div className="linha-do-tempo">
                {ordem.propostas_entrega.map((p) => (
                  <div key={p.id} className="evento">
                    <div className="evento-topo">
                      <Estado valor={p.estado} />
                      <small>{dataHora(p.criado_em)}</small>
                    </div>
                    <DetalheEntrega p={p} />
                    {p.justificativa_cliente && <p className="justificativa">Cliente: “{p.justificativa_cliente}”</p>}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <aside className="ordem-lateral">
          {orc && (
            <div className="cartao-orcamento">
              <h3>Orçamento final</h3>
              <dl className="custos">
                <div>
                  <dt>Materiais (qtd. {numero(orc.qtde_materiais)})</dt>
                  <dd>{moeda(orc.custo_materiais)}</dd>
                </div>
                <div>
                  <dt>
                    Mão de obra ({numero(orc.horas_marceneiro)} h × {moeda(orc.valor_hora)})
                    {!orc.mao_obra_confirmada && <em> estimada</em>}
                  </dt>
                  <dd>{moeda(orc.custo_mao_obra)}</dd>
                </div>
                <div>
                  <dt>Comissão do designer</dt>
                  <dd>{moeda(orc.comissao_designer)}</dd>
                </div>
                <div className="total">
                  <dt>Preço total</dt>
                  <dd>{moeda(orc.preco_total)}</dd>
                </div>
              </dl>
              {ordem.orcamento_id && (
                <Link para={`/orcamentos/${ordem.orcamento_id}`} className="botao botao-contorno botao-bloco">
                  Ver orçamento detalhado
                </Link>
              )}
            </div>
          )}

          <div className="cartao-lateral">
            <h3>Participantes</h3>
            <ul className="participantes">
              <li>
                <Avatar nome={n.cliente_nome} pequeno /> <span>{n.cliente_nome}</span> <small>Cliente</small>
              </li>
              <li>
                <Avatar nome={ordem.designer_nome} pequeno /> <span>{ordem.designer_nome}</span> <small>Designer</small>
              </li>
              <li>
                <Avatar nome={ordem.marceneiro_nome || '?'} pequeno /> <span>{ordem.marceneiro_nome || 'a definir'}</span>{' '}
                <small>Marceneiro</small>
              </li>
            </ul>
          </div>

          {ordem.propostas_marcenaria.length > 0 && (
            <div className="cartao-lateral">
              <h3>Propostas de marcenaria</h3>
              <ul className="propostas-marcenaria">
                {ordem.propostas_marcenaria.map((p) => (
                  <li key={p.id}>
                    <div>
                      <strong>{p.marceneiro_nome}</strong>
                      <small>
                        {numero(p.horas_trabalho)} h · {p.prazo_estimado_dias} dias
                      </small>
                    </div>
                    <div className="direita">
                      <span>{moeda(p.custo_execucao)}</span>
                      <Estado valor={p.status} />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {ordem.pagamentos.length > 0 && (
            <div className="cartao-lateral">
              <h3>Pagamentos</h3>
              <ul className="propostas-marcenaria">
                {ordem.pagamentos.map((p) => (
                  <li key={p.id}>
                    <div>
                      <strong>{p.tipo_servico_display}</strong>
                      <small>
                        {dataCurta(p.data_transacao)} · cartão final {p.cartao_final}
                      </small>
                    </div>
                    <div className="direita">
                      <span>{moeda(p.valor)}</span>
                      <Estado valor={p.status} />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>

      {escolhida && (
        <Checkout
          aberto
          titulo={`Contratar ${escolhida.marceneiro_nome}`}
          itens={[[`Mão de obra (${numero(escolhida.horas_trabalho)} h × ${moeda(escolhida.valor_hora)})`, escolhida.custo_execucao]]}
          total={escolhida.custo_execucao}
          observacao={`Prazo estimado de ${escolhida.prazo_estimado_dias} dias. As demais propostas de marcenaria serão recusadas.`}
          aoFechar={() => setEscolhida(null)}
          aoPagar={pagarMarceneiro}
        />
      )}
      <Visualizador src={arquivo} aoFechar={() => setArquivo(null)} />
    </div>
  )
}

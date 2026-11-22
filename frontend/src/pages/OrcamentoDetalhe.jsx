import { api, dataCurta, dataHora, moeda, numero } from '../api'
import { TabelaMateriais } from '../components/Propostas'
import { Alerta, Carregando, Estado, Voltar, useCarregar } from '../components/ui'
import { Link } from '../router'

// Composição do preço (barra segmentada) — paleta categórica validada (3 cores)
const PARTES = [
  ['custo_materiais', 'Materiais', 'var(--serie-1)'],
  ['custo_mao_obra', 'Mão de obra', 'var(--serie-2)'],
  ['comissao_designer', 'Comissão do designer', 'var(--serie-3)'],
]

function Composicao({ o }) {
  const total = Number(o.preco_total) || 0
  return (
    <div className="composicao">
      <div className="barra-segmentada" role="img" aria-label="Composição do preço total">
        {PARTES.map(([chave, rotulo, cor]) => {
          const v = Number(o[chave]) || 0
          if (!v || !total) return null
          const pct = (100 * v) / total
          return (
            <div key={chave} style={{ width: `${pct}%`, background: cor }} title={`${rotulo}: ${moeda(v)} (${Math.round(pct)}%)`}>
              {pct >= 12 && <span>{Math.round(pct)}%</span>}
            </div>
          )
        })}
      </div>
      <ul className="legenda">
        {PARTES.map(([chave, rotulo, cor]) => (
          <li key={chave}>
            <i style={{ background: cor }} />
            {rotulo} <b>{moeda(o[chave])}</b>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function OrcamentoDetalhe({ id }) {
  const { dados: o, carregando, erro } = useCarregar(() => api(`/orcamentos/${id}/`), [id])
  if (carregando && !o) return <Carregando />
  if (erro) return <div className="pagina"><Alerta>{erro.message}</Alerta></div>

  const pagos = o.pagamentos.filter((p) => p.status === 'APROVADO').reduce((s, p) => s + Number(p.valor), 0)

  return (
    <div className="pagina">
      <Voltar para="/orcamentos">Orçamentos</Voltar>
      <div className="orcamento-cabecalho">
        <div>
          <p className="codigo">Orçamento final · necessidade #{o.codigo} · OS #{o.ordem_id}</p>
          <h1>{o.titulo}</h1>
          <p className="texto-suave">
            {o.tipo_ambiente_display} · {o.cidade} · cliente {o.cliente_nome} · designer {o.designer_nome} · marceneiro{' '}
            {o.marceneiro_nome || 'a definir'}
          </p>
        </div>
        <div className="preco-total">
          <span>Preço total</span>
          <strong>{moeda(o.preco_total)}</strong>
          <Estado valor={o.ordem_estado} />
        </div>
      </div>

      <Composicao o={o} />

      <div className="orcamento-grade">
        <section className="bloco">
          <h2>1. Materiais (da proposta técnica)</h2>
          <TabelaMateriais materiais={o.materiais} />
          <h3 className="sub">Subtotais por tipo de material</h3>
          <table className="tabela tabela-compacta">
            <thead>
              <tr>
                <th>Tipo de material</th>
                <th className="num">Itens</th>
                <th className="num">Quantidade</th>
                <th className="num">Custo</th>
              </tr>
            </thead>
            <tbody>
              {o.materiais_por_tipo.map((g) => (
                <tr key={g.tipo_material}>
                  <td>{g.rotulo}</td>
                  <td className="num">{g.itens}</td>
                  <td className="num">{numero(g.quantidade)}</td>
                  <td className="num">{moeda(g.custo)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td>Total de materiais</td>
                <td className="num">{o.materiais.length}</td>
                <td className="num">{numero(o.qtde_materiais)}</td>
                <td className="num">{moeda(o.custo_materiais)}</td>
              </tr>
            </tfoot>
          </table>
        </section>

        <section className="bloco">
          <h2>2. Consolidação</h2>
          <table className="tabela tabela-consolidacao">
            <tbody>
              <tr>
                <td>
                  Materiais
                  <small>{numero(o.qtde_materiais)} unidades de material</small>
                </td>
                <td className="num">{moeda(o.custo_materiais)}</td>
              </tr>
              <tr>
                <td>
                  Mão de obra do marceneiro {!o.mao_obra_confirmada && <em>(estimativa)</em>}
                  <small>
                    {numero(o.horas_marceneiro)} h × {moeda(o.valor_hora)}/h
                  </small>
                </td>
                <td className="num">{moeda(o.custo_mao_obra)}</td>
              </tr>
              <tr>
                <td>
                  Comissão do designer (bônus)
                  <small>taxa de criatividade de {o.designer_nome}</small>
                </td>
                <td className="num">{moeda(o.comissao_designer)}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td>Preço total final</td>
                <td className="num">{moeda(o.preco_total)}</td>
              </tr>
            </tfoot>
          </table>
          {!o.mao_obra_confirmada && (
            <p className="nota">A mão de obra é estimada pelo designer até o cliente escolher um marceneiro; então o valor é recalculado.</p>
          )}
          <p className="nota">Atualizado em {dataHora(o.atualizado_em)}</p>

          {o.pagamentos.length > 0 && (
            <>
              <h3 className="sub">Pagamentos</h3>
              <table className="tabela tabela-compacta">
                <tbody>
                  {o.pagamentos.map((p) => (
                    <tr key={p.id}>
                      <td>
                        {p.tipo_servico_display}
                        <small className="texto-suave"> · {dataCurta(p.data_transacao)}</small>
                      </td>
                      <td>
                        <Estado valor={p.status} />
                      </td>
                      <td className="num">{moeda(p.valor)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan="2">Total pago</td>
                    <td className="num">{moeda(pagos)}</td>
                  </tr>
                </tfoot>
              </table>
            </>
          )}
          <Link para={`/ordens/${o.ordem_id}`} className="botao botao-contorno">
            Ver ordem de serviço
          </Link>
        </section>
      </div>
    </div>
  )
}

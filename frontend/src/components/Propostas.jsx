import { moeda, numero, VALOR_HORA_REFERENCIA } from '../api'
import { Avatar, Estado, PainelImagem } from './ui'

export function TabelaMateriais({ materiais }) {
  return (
    <div className="tabela-rolavel">
    <table className="tabela tabela-compacta">
      <thead>
        <tr>
          <th>Material</th>
          <th>Tipo</th>
          <th className="num">Qtd.</th>
          <th className="num">Unit.</th>
          <th className="num">Subtotal</th>
        </tr>
      </thead>
      <tbody>
        {materiais.map((m) => (
          <tr key={m.id}>
            <td>{m.descricao}</td>
            <td>{m.tipo_material_display}</td>
            <td className="num">
              {numero(m.quantidade)} {m.unidade_display}
            </td>
            <td className="num">{moeda(m.custo_unitario)}</td>
            <td className="num">{moeda(m.custo_total)}</td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  )
}

// Card de proposta técnica (desenho + materiais + custos), como no protótipo "Propostas"
export function CardPropostaTecnica({ proposta: p, aoVerArquivo, acao, mostrarEstado = true, titulo }) {
  return (
    <article className={`card-proposta ${p.estado === 'ARQUIVADA' ? 'apagada' : ''}`}>
      <div className="card-proposta-corpo">
        <header>
          <Avatar nome={p.designer_nome} pequeno />
          <div>
            <strong>{titulo || p.designer_nome}</strong>
            {titulo && <small>{p.designer_nome}</small>}
          </div>
          {mostrarEstado && <Estado valor={p.estado} />}
        </header>
        {p.descricao && <p className="descricao">{p.descricao}</p>}
        <TabelaMateriais materiais={p.materiais} />
        <dl className="custos">
          <div>
            <dt>Materiais ({p.materiais.length} {p.materiais.length === 1 ? 'item' : 'itens'})</dt>
            <dd>{moeda(p.custo_materiais)}</dd>
          </div>
          <div>
            <dt>Comissão do designer</dt>
            <dd>{moeda(p.comissao_designer)}</dd>
          </div>
          <div>
            <dt>
              Mão de obra estimada ({numero(p.horas_estimadas)} h × {moeda(VALOR_HORA_REFERENCIA)})
            </dt>
            <dd>{moeda(p.estimativa_mao_obra)}</dd>
          </div>
          <div className="total">
            <dt>Custo estimado</dt>
            <dd>{moeda(p.custo_estimado)}</dd>
          </div>
        </dl>
        {acao && <div className="acoes">{acao}</div>}
      </div>
      <div className="card-proposta-desenho">
        <PainelImagem src={p.desenho_tecnico} rotulo="Desenho técnico" grande onClick={() => aoVerArquivo?.(p.desenho_tecnico)} />
        <small>Desenho técnico · clique para ampliar</small>
      </div>
    </article>
  )
}

// Bloco com os dados da necessidade (painel superior dos protótipos)
export function PainelNecessidade({ n, aoVerArquivo, extra }) {
  return (
    <section className="painel-necessidade">
      <PainelImagem src={n.foto_ambiente} rotulo="Foto do ambiente" grande onClick={() => aoVerArquivo?.(n.foto_ambiente)} />
      <div className="painel-necessidade-info">
        <div className="titulo-linha">
          <h1>{n.titulo}</h1>
          {extra}
        </div>
        <p className="codigo">Necessidade #{n.codigo}</p>
        <div className="grade-info">
          <dl>
            <dt>Cidade</dt>
            <dd>{n.cidade}</dd>
            <dt>Ambiente</dt>
            <dd>{n.tipo_ambiente_display}</dd>
            <dt>Altura × Largura × Profundidade</dt>
            <dd>
              {numero(n.altura)} × {numero(n.largura)} × {numero(n.profundidade)} cm
            </dd>
            <dt>Custo esperado</dt>
            <dd>{moeda(n.custo_esperado)}</dd>
            {n.cliente_nome && (
              <>
                <dt>Cliente</dt>
                <dd>{n.cliente_nome}</dd>
              </>
            )}
          </dl>
          <div>
            <span className="rotulo-solto">Observações adicionais</span>
            <p className="observacoes">{n.observacoes || '—'}</p>
            {n.esboco_movel && (
              <button type="button" className="mini-arquivo" onClick={() => aoVerArquivo?.(n.esboco_movel)}>
                Ver esboço do móvel enviado pelo cliente
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

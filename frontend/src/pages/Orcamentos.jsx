import { useState } from 'react'
import { api, moeda, numero } from '../api'
import { useAuth } from '../auth'
import { Alerta, Carregando, Estado, Vazio, useCarregar } from '../components/ui'
import { Link, navegar } from '../router'

const DIMENSOES = [
  ['tipo_ambiente', 'Tipo de ambiente'],
  ['tipo_material', 'Tipo de material'],
  ['estado', 'Estado da OS'],
  ['mes', 'Mês'],
  ['cidade', 'Cidade'],
  ['designer', 'Designer'],
  ['marceneiro', 'Marceneiro'],
]

const MEDIDAS = [
  ['preco_total', 'Preço total', true],
  ['custo_materiais', 'Custo de materiais', true],
  ['custo_mao_obra', 'Mão de obra', true],
  ['comissao_designer', 'Comissão do designer', true],
  ['horas_marceneiro', 'Horas de marcenaria', false],
  ['qtde_materiais', 'Qtde. de materiais', false],
  ['quantidade_projetos', 'Projetos', false],
]
const MEDIDAS_MATERIAL = ['quantidade_projetos', 'qtde_materiais', 'custo_materiais']
const CURTO = {
  quantidade_projetos: 'Projetos',
  qtde_materiais: 'Qtd. mat.',
  custo_materiais: 'Materiais',
  horas_marceneiro: 'Horas',
  custo_mao_obra: 'Mão de obra',
  comissao_designer: 'Comissão',
  preco_total: 'Preço total',
}
const ehMoeda = (m) => MEDIDAS.find((x) => x[0] === m)?.[2]
const formatar = (m, v) => (ehMoeda(m) ? moeda(v) : numero(v))

function compacto(v) {
  const n = Number(v) || 0
  if (n >= 1e6) return `R$ ${numero(n / 1e6)} mi`
  if (n >= 1e4) return `R$ ${numero(Math.round(n / 100) / 10)} mil`
  return moeda(n)
}

function Kpis({ total, tipo }) {
  const tiles = [
    ['Projetos', numero(total.quantidade_projetos), null],
    ['Preço total consolidado', compacto(total.preco_total), 'preco_total'],
    ['Materiais', compacto(total.custo_materiais), 'custo_materiais'],
    ['Mão de obra', compacto(total.custo_mao_obra), 'custo_mao_obra'],
    ['Comissões de designers', compacto(total.comissao_designer), 'comissao_designer'],
    ['Horas de marcenaria', `${numero(total.horas_marceneiro)} h`, null],
  ]
  const foco = { CLIENTE: 'preco_total', DESIGNER: 'comissao_designer', MARCENEIRO: 'custo_mao_obra' }[tipo]
  return (
    <div className="kpis">
      {tiles.map(([rotulo, valor, chave]) => (
        <div key={rotulo} className={`kpi ${chave === foco ? 'foco' : ''}`}>
          <span>{rotulo}</span>
          <strong>{valor}</strong>
        </div>
      ))}
    </div>
  )
}

// Totalização por UMA dimensão: todas as medidas + linha de total
function TabelaTotalizacao({ dados }) {
  const medidas = dados.medidas.map((m) => m.chave)
  const barra = medidas.includes('preco_total') ? 'preco_total' : 'custo_materiais'
  const max = Math.max(...dados.linhas.map((l) => Number(l[barra]) || 0), 1)
  return (
    <div className="tabela-rolavel">
      <table className="tabela tabela-totalizacao">
        <thead>
          <tr>
            <th>{dados.dimensao_rotulo}</th>
            {dados.medidas.map((m) => (
              <th key={m.chave} className="num">
                {CURTO[m.chave] || m.rotulo}
              </th>
            ))}
            <th className="col-barra">Participação</th>
          </tr>
        </thead>
        <tbody>
          {dados.linhas.map((l) => (
            <tr key={l.chave}>
              <td>{l.rotulo}</td>
              {medidas.map((m) => (
                <td key={m} className="num">
                  {formatar(m, l[m])}
                </td>
              ))}
              <td className="col-barra">
                <div className="barra-trilho" title={`${l.rotulo}: ${formatar(barra, l[barra])}`}>
                  <div className="barra" style={{ width: `${(100 * (Number(l[barra]) || 0)) / max}%` }} />
                </div>
                <small>{dados.total[barra] ? `${Math.round((100 * l[barra]) / dados.total[barra])}%` : '—'}</small>
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td>Total geral</td>
            {medidas.map((m) => (
              <td key={m} className="num">
                {formatar(m, dados.total[m])}
              </td>
            ))}
            <td />
          </tr>
        </tfoot>
      </table>
    </div>
  )
}

// Cubo: cruzamento de duas dimensões para uma medida, com totais de linha e coluna
function TabelaCubo({ dados }) {
  const m = dados.medida
  return (
    <div className="tabela-rolavel">
      <table className="tabela tabela-cubo">
        <thead>
          <tr>
            <th>
              {DIMENSOES.find((d) => d[0] === dados.linhas_dimensao)?.[1]} ↓ / {DIMENSOES.find((d) => d[0] === dados.colunas_dimensao)?.[1]} →
            </th>
            {dados.colunas.map((c) => (
              <th key={c.chave} className="num">
                {c.rotulo}
              </th>
            ))}
            <th className="num">Total</th>
          </tr>
        </thead>
        <tbody>
          {dados.linhas.map((l) => (
            <tr key={l.chave}>
              <td>{l.rotulo}</td>
              {dados.colunas.map((c) => {
                const v = dados.celulas[l.chave]?.[c.chave]
                return (
                  <td key={c.chave} className={`num ${v === undefined ? 'vazia' : ''}`}>
                    {v === undefined ? '—' : formatar(m, v)}
                  </td>
                )
              })}
              <td className="num total-col">{formatar(m, dados.total_linhas[l.chave])}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td>Total</td>
            {dados.colunas.map((c) => (
              <td key={c.chave} className="num">
                {formatar(m, dados.total_colunas[c.chave])}
              </td>
            ))}
            <td className="num">{formatar(m, dados.total_geral)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}

export default function Orcamentos() {
  const { usuario } = useAuth()
  const [dimensao, setDimensao] = useState('tipo_ambiente')
  const [linhas, setLinhas] = useState('tipo_ambiente')
  const [colunas, setColunas] = useState('estado')
  const [medida, setMedida] = useState('preco_total')

  const comMaterial = linhas === 'tipo_material' || colunas === 'tipo_material'
  const medidaEfetiva = comMaterial && !MEDIDAS_MATERIAL.includes(medida) ? 'custo_materiais' : medida

  const lista = useCarregar(() => api('/orcamentos/'))
  const geral = useCarregar(() => api('/orcamentos/totalizacao/?dimensao=estado'))
  const tot = useCarregar(() => api(`/orcamentos/totalizacao/?dimensao=${dimensao}`), [dimensao])
  const cubo = useCarregar(
    () => api(`/orcamentos/cubo/?linhas=${linhas}&colunas=${colunas}&medida=${medidaEfetiva}`),
    [linhas, colunas, medidaEfetiva],
  )

  if (lista.carregando && !lista.dados) return <Carregando />
  const orcamentos = lista.dados || []

  return (
    <div className="pagina">
      <div className="pagina-topo">
        <div>
          <h1>Orçamentos</h1>
          <p className="texto-suave">
            Entidade multidimensional <b>Orçamento Final</b>: cada projeto cruza materiais (proposta técnica), mão de obra (proposta do
            marceneiro) e comissão do designer.
          </p>
        </div>
      </div>
      {lista.erro && <Alerta>{lista.erro.message}</Alerta>}

      {orcamentos.length === 0 ? (
        <Vazio titulo="Nenhum orçamento ainda">Os orçamentos são gerados quando um cliente aprova uma proposta técnica.</Vazio>
      ) : (
        <>
          {geral.dados && <Kpis total={geral.dados.total} tipo={usuario.tipo} />}

          <section className="bloco">
            <div className="bloco-topo">
              <h2>Totalização por dimensão</h2>
              <div className="abas abas-rolaveis">
                {DIMENSOES.map(([v, r]) => (
                  <button key={v} className={dimensao === v ? 'ativa' : ''} onClick={() => setDimensao(v)}>
                    {r}
                  </button>
                ))}
              </div>
            </div>
            {tot.erro && <Alerta>{tot.erro.message}</Alerta>}
            {tot.dados ? <TabelaTotalizacao dados={tot.dados} /> : <Carregando />}
          </section>

          <section className="bloco">
            <div className="bloco-topo">
              <h2>Cubo — cruzamento de dimensões</h2>
              <div className="filtros compactos">
                <label>
                  Linhas
                  <select value={linhas} onChange={(e) => setLinhas(e.target.value)}>
                    {DIMENSOES.map(([v, r]) => (
                      <option key={v} value={v}>
                        {r}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Colunas
                  <select value={colunas} onChange={(e) => setColunas(e.target.value)}>
                    {DIMENSOES.map(([v, r]) => (
                      <option key={v} value={v}>
                        {r}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Medida
                  <select value={medidaEfetiva} onChange={(e) => setMedida(e.target.value)}>
                    {MEDIDAS.filter(([v]) => !comMaterial || MEDIDAS_MATERIAL.includes(v)).map(([v, r]) => (
                      <option key={v} value={v}>
                        {r}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
            {cubo.erro && <Alerta>{cubo.erro.message}</Alerta>}
            {cubo.dados ? <TabelaCubo dados={cubo.dados} /> : <Carregando />}
          </section>

          <section className="bloco">
            <div className="bloco-topo">
              <h2>Orçamentos finais</h2>
              <span className="texto-suave">{orcamentos.length} projeto(s)</span>
            </div>
            <div className="tabela-rolavel">
              <table className="tabela tabela-clicavel">
                <thead>
                  <tr>
                    <th>Projeto</th>
                    <th>Ambiente</th>
                    <th>Estado</th>
                    <th className="num">Materiais</th>
                    <th className="num">Mão de obra</th>
                    <th className="num">Comissão</th>
                    <th className="num">Preço total</th>
                  </tr>
                </thead>
                <tbody>
                  {orcamentos.map((o) => (
                    <tr key={o.id} onClick={() => navegar(`/orcamentos/${o.id}`)}>
                      <td>
                        <Link para={`/orcamentos/${o.id}`}>{o.titulo}</Link>
                        <small className="codigo"> #{o.codigo}</small>
                      </td>
                      <td>{o.tipo_ambiente_display}</td>
                      <td>
                        <Estado valor={o.ordem_estado} />
                      </td>
                      <td className="num">{moeda(o.custo_materiais)}</td>
                      <td className="num">
                        {moeda(o.custo_mao_obra)}
                        {!o.mao_obra_confirmada && <small className="texto-suave"> est.</small>}
                      </td>
                      <td className="num">{moeda(o.comissao_designer)}</td>
                      <td className="num forte">{moeda(o.preco_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  )
}

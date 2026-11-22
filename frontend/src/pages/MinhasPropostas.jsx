import { useState } from 'react'
import { api, dataCurta, moeda } from '../api'
import { Alerta, CardProjeto, Carregando, Estado, Vazio, useCarregar } from '../components/ui'
import { navegar } from '../router'

const ABAS = [
  ['', 'Todas'],
  ['SUBMETIDA', 'Aguardando cliente'],
  ['APROVADA', 'Aprovadas'],
  ['ARQUIVADA', 'Arquivadas'],
]

export default function MinhasPropostas() {
  const [aba, setAba] = useState('')
  const { dados, carregando, erro } = useCarregar(() => api('/propostas-tecnicas/'))
  const lista = (dados || []).filter((p) => !aba || p.estado === aba)
  const aprovadas = (dados || []).filter((p) => p.estado === 'APROVADA')
  const comissoes = aprovadas.reduce((s, p) => s + Number(p.comissao_designer), 0)

  return (
    <div className="pagina">
      <div className="pagina-topo">
        <div>
          <h1>Minhas propostas</h1>
          <p className="texto-suave">
            {aprovadas.length} aprovada(s) · {moeda(comissoes)} em comissões
          </p>
        </div>
        <div className="abas">
          {ABAS.map(([v, r]) => (
            <button key={v} className={aba === v ? 'ativa' : ''} onClick={() => setAba(v)}>
              {r}
            </button>
          ))}
        </div>
      </div>
      {erro && <Alerta>{erro.message}</Alerta>}
      {carregando && !dados ? (
        <Carregando />
      ) : lista.length === 0 ? (
        <Vazio titulo="Nenhuma proposta aqui">Envie propostas pelo mural de projetos disponíveis.</Vazio>
      ) : (
        <div className="grade-cards">
          {lista.map((p) => (
            <CardProjeto
              key={p.id}
              imagem={p.desenho_tecnico}
              titulo={p.necessidade_titulo}
              canto={<span className="codigo">#{p.necessidade_codigo}</span>}
              linhas={[`Enviada em ${dataCurta(p.criado_em)}`, `Custo estimado ${moeda(p.custo_estimado)}`, `Comissão ${moeda(p.comissao_designer)}`]}
              rodape={<Estado valor={p.estado} />}
              onClick={() => navegar(p.ordem_id ? `/ordens/${p.ordem_id}` : `/projetos/${p.necessidade}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

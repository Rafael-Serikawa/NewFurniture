import { useState } from 'react'
import { AMBIENTES, api, medidas, moeda } from '../api'
import { Alerta, Avatar, CardProjeto, Carregando, Vazio, useCarregar } from '../components/ui'
import { navegar } from '../router'

// Mural de necessidades "Abertas" (DES001 passo 1) — visão do designer
export default function ProjetosDisponiveis() {
  const [ambiente, setAmbiente] = useState('')
  const [cidade, setCidade] = useState('')
  const [busca, setBusca] = useState('')

  const query = new URLSearchParams({ estado: 'ABERTA' })
  if (ambiente) query.set('tipo_ambiente', ambiente)
  if (cidade) query.set('cidade', cidade)
  const { dados, carregando, erro } = useCarregar(() => api(`/necessidades/?${query}`), [ambiente, cidade])

  const lista = (dados || []).filter((n) => !busca || n.titulo.toLowerCase().includes(busca.toLowerCase()))

  return (
    <div className="pagina">
      <div className="pagina-topo">
        <div>
          <h1>Projetos disponíveis</h1>
          <p className="texto-suave">Necessidades abertas publicadas por clientes. Escolha uma e envie seu desenho técnico.</p>
        </div>
      </div>
      <div className="filtros">
        <input placeholder="Buscar por título…" value={busca} onChange={(e) => setBusca(e.target.value)} />
        <select value={ambiente} onChange={(e) => setAmbiente(e.target.value)}>
          <option value="">Todos os ambientes</option>
          {AMBIENTES.map(([v, r]) => (
            <option key={v} value={v}>
              {r}
            </option>
          ))}
        </select>
        <input placeholder="Cidade" value={cidade} onChange={(e) => setCidade(e.target.value)} />
      </div>
      {erro && <Alerta>{erro.message}</Alerta>}
      {carregando && !dados ? (
        <Carregando />
      ) : lista.length === 0 ? (
        <Vazio titulo="Nenhuma necessidade aberta encontrada">Tente outros filtros ou volte mais tarde.</Vazio>
      ) : (
        <div className="grade-cards">
          {lista.map((n) => (
            <CardProjeto
              key={n.id}
              imagem={n.foto_ambiente}
              titulo={n.titulo}
              canto={<Avatar nome={n.cliente_nome} pequeno />}
              linhas={[`${n.tipo_ambiente_display} · ${n.cidade}`, medidas(n), `Até ${moeda(n.custo_esperado)}`]}
              rodape={
                n.ja_propus ? (
                  <span className="estado estado-verde">Proposta enviada</span>
                ) : (
                  <span className="texto-suave">
                    {n.total_propostas ? `${n.total_propostas} proposta(s) concorrente(s)` : 'Seja o primeiro a propor'}
                  </span>
                )
              }
              onClick={() => navegar(`/projetos/${n.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

import { api, dataCurta, medidas, moeda } from '../api'
import { useAuth } from '../auth'
import { Alerta, CardProjeto, Carregando, Estado, Vazio, useCarregar } from '../components/ui'
import { navegar } from '../router'

// Aba de histórico de projetos concluídos (extensão do ENT002, v1.3)
export default function Historico() {
  const { usuario } = useAuth()
  const { dados, carregando, erro } = useCarregar(() => api('/ordens/?escopo=historico'))
  const lista = dados || []
  const total = lista.reduce((s, o) => s + Number(o.preco_total || 0), 0)

  return (
    <div className="pagina">
      <div className="pagina-topo">
        <div>
          <h1>Histórico</h1>
          <p className="texto-suave">
            {lista.length} projeto(s) concluído(s)
            {usuario.tipo === 'CLIENTE' && lista.length > 0 && ` · ${moeda(total)} investidos`}
          </p>
        </div>
      </div>
      {erro && <Alerta>{erro.message}</Alerta>}
      {carregando && !dados ? (
        <Carregando />
      ) : lista.length === 0 ? (
        <Vazio titulo="Nenhum projeto concluído ainda">Os projetos entregues aparecem aqui.</Vazio>
      ) : (
        <div className="grade-cards">
          {lista.map((o) => (
            <CardProjeto
              key={o.id}
              imagem={o.necessidade.foto_ambiente}
              titulo={o.necessidade.titulo}
              canto={<span className="codigo">#{o.necessidade.codigo}</span>}
              linhas={[
                `${o.necessidade.tipo_ambiente_display} · ${medidas(o.necessidade)}`,
                usuario.tipo === 'CLIENTE' ? `Designer ${o.designer_nome} · Marceneiro ${o.marceneiro_nome}` : `Cliente ${o.necessidade.cliente_nome}`,
                `Iniciado em ${dataCurta(o.data_inicio)} · ${moeda(o.preco_total)}`,
              ]}
              rodape={<Estado valor="ENTREGUE" rotulo="Está entregue" />}
              onClick={() => navegar(`/ordens/${o.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

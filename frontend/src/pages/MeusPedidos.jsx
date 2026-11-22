import { useState } from 'react'
import { AMBIENTES, api, medidas, paraFormData } from '../api'
import { useAuth } from '../auth'
import { Alerta, Campo, CardProjeto, Carregando, Estado, Icone, Modal, SeletorArquivo, useCarregar, useToast } from '../components/ui'
import { navegar } from '../router'

const VAZIO = {
  titulo: '',
  cidade: '',
  tipo_ambiente: 'COZINHA',
  largura: '',
  altura: '',
  profundidade: '',
  custo_esperado: '',
  observacoes: '',
}

const extensao = (f) => (f?.name.split('.').pop() || '').toLowerCase()

// NEC001 - Cadastro de necessidade de móvel
function NovaNecessidade({ aberto, aoFechar, aoCriar }) {
  const { usuario } = useAuth()
  const [form, setForm] = useState({ ...VAZIO, cidade: usuario?.cidade || '' })
  const [foto, setFoto] = useState(null)
  const [esboco, setEsboco] = useState(null)
  const [erros, setErros] = useState({})
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const mudar = (c) => (e) => {
    setForm((f) => ({ ...f, [c]: e.target.value }))
    setErros((es) => ({ ...es, [c]: undefined }))
  }

  const validar = () => {
    const e = {}
    if (!form.titulo.trim()) e.titulo = 'Obrigatório.'
    if (!form.cidade.trim()) e.cidade = 'Obrigatório.'
    for (const m of ['largura', 'altura', 'profundidade']) if (!(Number(form[m]) > 0)) e[m] = 'Maior que zero.'
    if (form.custo_esperado === '' || Number(form.custo_esperado) < 0 || !Number.isInteger(Number(form.custo_esperado)))
      e.custo_esperado = 'Inteiro maior ou igual a zero.'
    if (!foto) e.foto_ambiente = 'A foto do ambiente é obrigatória.'
    else if (!['jpg', 'jpeg', 'png'].includes(extensao(foto))) e.foto_ambiente = 'Use JPG ou PNG.'
    if (esboco && !['jpg', 'jpeg', 'png', 'pdf'].includes(extensao(esboco))) e.esboco_movel = 'Use JPG, PNG ou PDF.'
    return e
  }

  const enviar = async (ev) => {
    ev.preventDefault()
    setErro('')
    const e = validar()
    setErros(e)
    if (Object.keys(e).length) return setErro('Dados inválidos: corrija os campos destacados.')
    setEnviando(true)
    try {
      const criada = await api('/necessidades/', {
        method: 'POST',
        form: paraFormData({ ...form, foto_ambiente: foto, esboco_movel: esboco }),
      })
      setForm({ ...VAZIO, cidade: usuario?.cidade || '' })
      setFoto(null)
      setEsboco(null)
      setErros({})
      aoCriar(criada)
    } catch (err) {
      setErro(err.message)
      setErros(err.campos)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal aberto={aberto} aoFechar={aoFechar} largura={900} titulo="Nova necessidade">
      <form className="modal-dividido" onSubmit={enviar} noValidate>
        <SeletorArquivo
          arquivo={esboco}
          aoEscolher={(f) => {
            setEsboco(f)
            setErros((es) => ({ ...es, esboco_movel: undefined }))
          }}
          rotulo="Adicionar imagem do esboço (opcional)"
          aceitar="image/png,image/jpeg,application/pdf"
          erro={erros.esboco_movel}
        />
        <div className="modal-conteudo">
          <h2>Descreva seu projeto</h2>
          <Alerta>{erro}</Alerta>
          <div className="grade-form">
            <div>
              <Campo rotulo="Título do projeto" erro={erros.titulo}>
                <input value={form.titulo} onChange={mudar('titulo')} maxLength={100} placeholder="Ex.: Armário para cozinha" />
              </Campo>
              <Campo rotulo="Cidade" erro={erros.cidade}>
                <input value={form.cidade} onChange={mudar('cidade')} maxLength={100} />
              </Campo>
              <Campo rotulo="Tipo de ambiente" erro={erros.tipo_ambiente}>
                <select value={form.tipo_ambiente} onChange={mudar('tipo_ambiente')}>
                  {AMBIENTES.map(([v, r]) => (
                    <option key={v} value={v}>
                      {r}
                    </option>
                  ))}
                </select>
              </Campo>
              <div className="linha-campos tres">
                <Campo rotulo="Altura (cm)" erro={erros.altura}>
                  <input type="number" min="0" step="0.1" value={form.altura} onChange={mudar('altura')} />
                </Campo>
                <Campo rotulo="Largura (cm)" erro={erros.largura}>
                  <input type="number" min="0" step="0.1" value={form.largura} onChange={mudar('largura')} />
                </Campo>
                <Campo rotulo="Profund. (cm)" erro={erros.profundidade}>
                  <input type="number" min="0" step="0.1" value={form.profundidade} onChange={mudar('profundidade')} />
                </Campo>
              </div>
            </div>
            <div>
              <Campo bloco rotulo="Foto do ambiente (JPG/PNG)" erro={erros.foto_ambiente}>
                <SeletorArquivo
                  arquivo={foto}
                  aoEscolher={(f) => {
                    setFoto(f)
                    setErros((es) => ({ ...es, foto_ambiente: undefined }))
                  }}
                  rotulo="Escolher foto"
                  grande={false}
                />
              </Campo>
              <Campo rotulo="Custo esperado (R$)" erro={erros.custo_esperado}>
                <input type="number" min="0" step="1" value={form.custo_esperado} onChange={mudar('custo_esperado')} />
              </Campo>
              <Campo rotulo="Observações adicionais" erro={erros.observacoes} dica={`${form.observacoes.length}/700`}>
                <textarea rows="4" maxLength={700} value={form.observacoes} onChange={mudar('observacoes')} />
              </Campo>
            </div>
          </div>
          <div className="acoes">
            <button type="button" className="botao botao-texto" onClick={aoFechar}>
              Cancelar
            </button>
            <button className="botao" disabled={enviando}>
              {enviando ? 'Enviando…' : 'Enviar solicitação'}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  )
}

function estadoDoPedido(n) {
  if (n.estado === 'ABERTA')
    return n.total_propostas ? (
      <span className="texto-suave">
        {n.total_propostas} proposta{n.total_propostas > 1 ? 's' : ''} recebida{n.total_propostas > 1 ? 's' : ''}
      </span>
    ) : (
      <span className="texto-suave">Aguardando propostas</span>
    )
  return <Estado valor={n.ordem_estado} />
}

const FILTROS = [
  ['andamento', 'Em andamento'],
  ['concluidos', 'Concluídos'],
  ['todos', 'Todos'],
]

export default function MeusPedidos() {
  const toast = useToast()
  const [novo, setNovo] = useState(false)
  const [filtro, setFiltro] = useState('andamento')
  const { dados, carregando, erro, recarregar } = useCarregar(() => api('/necessidades/'))

  const lista = (dados || []).filter((n) =>
    filtro === 'todos' ? true : filtro === 'concluidos' ? n.ordem_estado === 'ENTREGUE' : n.ordem_estado !== 'ENTREGUE',
  )

  return (
    <div className="pagina">
      <div className="pagina-topo">
        <h1>Meus pedidos</h1>
        <div className="abas">
          {FILTROS.map(([v, r]) => (
            <button key={v} className={filtro === v ? 'ativa' : ''} onClick={() => setFiltro(v)}>
              {r}
            </button>
          ))}
        </div>
      </div>
      {erro && <Alerta>{erro.message}</Alerta>}
      {carregando && !dados ? (
        <Carregando />
      ) : (
        <div className="grade-cards">
          {filtro !== 'concluidos' && (
            <button className="card-novo" onClick={() => setNovo(true)}>
              <span className="card-novo-icone">
                <Icone.mais />
              </span>
              <strong>Adicionar novo pedido</strong>
            </button>
          )}
          {lista.map((n) => (
            <CardProjeto
              key={n.id}
              imagem={n.foto_ambiente}
              titulo={n.titulo}
              linhas={[`${n.tipo_ambiente_display} · ${n.cidade}`, medidas(n)]}
              rodape={estadoDoPedido(n)}
              canto={<span className="codigo">#{n.codigo}</span>}
              contador={n.estado === 'ABERTA' ? n.propostas_submetidas : 0}
              onClick={() => navegar(n.ordem_id ? `/ordens/${n.ordem_id}` : `/pedidos/${n.id}`)}
            />
          ))}
        </div>
      )}
      <NovaNecessidade
        aberto={novo}
        aoFechar={() => setNovo(false)}
        aoCriar={(n) => {
          setNovo(false)
          toast(`Necessidade publicada com sucesso! Código ${n.codigo} — já visível para a rede de designers.`)
          recarregar()
        }}
      />
    </div>
  )
}

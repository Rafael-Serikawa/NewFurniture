import { useState } from 'react'
import { api, moeda, numero, paraFormData, TIPOS_MATERIAL, UNIDADES, VALOR_HORA_REFERENCIA } from '../api'
import { CardPropostaTecnica, PainelNecessidade } from '../components/Propostas'
import { Alerta, Campo, Carregando, Estado, Icone, SeletorArquivo, Visualizador, Voltar, useCarregar, useToast } from '../components/ui'
import { Link } from '../router'

const NOVO_MATERIAL = () => ({ tipo_material: 'MDF', descricao: '', quantidade: '', unidade: 'm2', custo_unitario: '' })

// DES001 - Inclusão de desenho técnico
function FormProposta({ necessidade, aoEnviar }) {
  const [desenho, setDesenho] = useState(null)
  const [materiais, setMateriais] = useState([NOVO_MATERIAL()])
  const [comissao, setComissao] = useState('')
  const [horas, setHoras] = useState('')
  const [descricao, setDescricao] = useState('')
  const [erros, setErros] = useState({})
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const mudarMaterial = (i, campo, valor) => setMateriais((ms) => ms.map((m, j) => (j === i ? { ...m, [campo]: valor } : m)))
  const subtotal = (m) => (Number(m.quantidade) || 0) * (Number(m.custo_unitario) || 0)
  const custoMateriais = materiais.reduce((s, m) => s + subtotal(m), 0)
  const qtdMateriais = materiais.reduce((s, m) => s + (Number(m.quantidade) || 0), 0)
  const maoObra = (Number(horas) || 0) * VALOR_HORA_REFERENCIA
  const total = custoMateriais + (Number(comissao) || 0) + maoObra
  const acimaDoEsperado = total > Number(necessidade.custo_esperado)

  const validar = () => {
    const e = {}
    if (!desenho) e.desenho_tecnico = 'Envie o desenho técnico (JPG, PNG ou PDF).'
    else if (!/\.(jpe?g|png|pdf)$/i.test(desenho.name))
      e.desenho_tecnico = 'Formato não suportado. Envie em JPG, PNG ou PDF (exporte o seu DWG para PDF).'
    if (comissao === '' || Number(comissao) < 0) e.comissao_designer = 'Informe um valor maior ou igual a zero.'
    if (horas !== '' && Number(horas) < 0) e.horas_estimadas = 'Não pode ser negativo.'
    const ruins = materiais.some((m) => !m.descricao.trim() || !(Number(m.quantidade) > 0) || m.custo_unitario === '' || Number(m.custo_unitario) < 0)
    if (ruins) e.materiais = 'Preencha descrição, quantidade (> 0) e custo unitário (≥ 0) de todos os materiais.'
    return e
  }

  const enviar = async (ev) => {
    ev.preventDefault()
    setErro('')
    const e = validar()
    setErros(e)
    if (Object.keys(e).length) return setErro('Corrija os campos destacados antes de enviar.')
    setEnviando(true)
    try {
      await api('/propostas-tecnicas/', {
        method: 'POST',
        form: paraFormData({
          necessidade: necessidade.id,
          desenho_tecnico: desenho,
          comissao_designer: comissao,
          horas_estimadas: horas || '0',
          descricao,
          materiais: JSON.stringify(materiais),
        }),
      })
      aoEnviar()
    } catch (err) {
      setErro(err.message)
      setErros(err.campos)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="form-proposta" onSubmit={enviar} noValidate>
      <div className="form-proposta-desenho">
        <SeletorArquivo
          arquivo={desenho}
          aoEscolher={(f) => {
            setDesenho(f)
            setErros(({ desenho_tecnico, ...resto }) => resto)
          }}
          rotulo="Adicionar desenho técnico (JPG/PNG/PDF)"
          aceitar="image/png,image/jpeg,application/pdf"
          erro={erros.desenho_tecnico}
        />
      </div>
      <div className="form-proposta-dados">
        <h2>Enviar proposta</h2>
        <Alerta>{erro}</Alerta>
        <div className="campo-rotulo">Lista de materiais e quantidade</div>
        <div className="editor-materiais">
          <div className="editor-linha cabecalho">
            <span>Tipo</span>
            <span>Descrição</span>
            <span>Qtd.</span>
            <span>Un.</span>
            <span>Custo unit. (R$)</span>
            <span className="num">Subtotal</span>
            <span />
          </div>
          {materiais.map((m, i) => (
            <div className="editor-linha" key={i}>
              <select value={m.tipo_material} onChange={(e) => mudarMaterial(i, 'tipo_material', e.target.value)} aria-label="Tipo de material">
                {TIPOS_MATERIAL.map(([v, r]) => (
                  <option key={v} value={v}>
                    {r}
                  </option>
                ))}
              </select>
              <input value={m.descricao} maxLength={120} placeholder="Ex.: Chapa MDF 18 mm" onChange={(e) => mudarMaterial(i, 'descricao', e.target.value)} aria-label="Descrição" />
              <input type="number" min="0" step="0.01" value={m.quantidade} onChange={(e) => mudarMaterial(i, 'quantidade', e.target.value)} aria-label="Quantidade" />
              <select value={m.unidade} onChange={(e) => mudarMaterial(i, 'unidade', e.target.value)} aria-label="Unidade">
                {UNIDADES.map(([v, r]) => (
                  <option key={v} value={v}>
                    {r}
                  </option>
                ))}
              </select>
              <input type="number" min="0" step="0.01" value={m.custo_unitario} onChange={(e) => mudarMaterial(i, 'custo_unitario', e.target.value)} aria-label="Custo unitário" />
              <span className="num">{moeda(subtotal(m))}</span>
              <button type="button" className="botao-icone" disabled={materiais.length === 1} onClick={() => setMateriais((ms) => ms.filter((_, j) => j !== i))} aria-label="Remover material">
                <Icone.lixo />
              </button>
            </div>
          ))}
          {erros.materiais && <small className="erro-campo">{erros.materiais}</small>}
          <button type="button" className="botao botao-contorno botao-pequeno" onClick={() => setMateriais((ms) => [...ms, NOVO_MATERIAL()])}>
            + Adicionar material
          </button>
        </div>

        <div className="linha-campos">
          <Campo rotulo="Comissão do designer (R$)" erro={erros.comissao_designer}>
            <input type="number" min="0" step="0.01" value={comissao} onChange={(e) => {
              setComissao(e.target.value)
              setErros(({ comissao_designer, ...resto }) => resto)
            }} />
          </Campo>
          <Campo rotulo="Horas de marcenaria estimadas" erro={erros.horas_estimadas} dica={`Referência: ${moeda(VALOR_HORA_REFERENCIA)}/h`}>
            <input type="number" min="0" step="0.5" value={horas} onChange={(e) => setHoras(e.target.value)} />
          </Campo>
        </div>
        <Campo rotulo="Descrição da solução (opcional)" erro={erros.descricao}>
          <textarea rows="3" maxLength={1000} value={descricao} onChange={(e) => setDescricao(e.target.value)} />
        </Campo>

        <dl className="custos resumo-vivo">
          <div>
            <dt>Materiais ({materiais.length} {materiais.length === 1 ? 'item' : 'itens'} · qtd. {numero(qtdMateriais)})</dt>
            <dd>{moeda(custoMateriais)}</dd>
          </div>
          <div>
            <dt>Comissão do designer</dt>
            <dd>{moeda(Number(comissao) || 0)}</dd>
          </div>
          <div>
            <dt>Mão de obra estimada</dt>
            <dd>{moeda(maoObra)}</dd>
          </div>
          <div className="total">
            <dt>Custo estimado</dt>
            <dd>{moeda(total)}</dd>
          </div>
        </dl>
        {acimaDoEsperado && (
          <Alerta tipo="aviso">O custo estimado está acima do custo esperado pelo cliente ({moeda(necessidade.custo_esperado)}).</Alerta>
        )}
        <div className="acoes">
          <Link para="/projetos" className="botao botao-texto">
            Cancelar
          </Link>
          <button className="botao" disabled={enviando}>
            {enviando ? 'Enviando…' : 'Enviar proposta'}
          </button>
        </div>
      </div>
    </form>
  )
}

export default function ProjetoDesigner({ id }) {
  const toast = useToast()
  const [arquivo, setArquivo] = useState(null)
  const { dados: n, carregando, erro, recarregar } = useCarregar(() => api(`/necessidades/${id}/`), [id])

  if (carregando && !n) return <Carregando />
  if (erro) return <div className="pagina"><Alerta>{erro.message}</Alerta></div>
  const minha = n.propostas[0]

  return (
    <div className="pagina">
      <Voltar para="/projetos">Projetos disponíveis</Voltar>
      <PainelNecessidade n={n} aoVerArquivo={setArquivo} extra={<Estado valor={n.estado} />} />
      {minha ? (
        <>
          <div className="secao-titulo">
            <h2>Sua proposta</h2>
            {minha.ordem_id && <Link para={`/ordens/${minha.ordem_id}`}>Acompanhar a fabricação →</Link>}
          </div>
          <CardPropostaTecnica proposta={minha} aoVerArquivo={setArquivo} />
        </>
      ) : n.estado === 'ABERTA' ? (
        <FormProposta
          necessidade={n}
          aoEnviar={() => {
            toast('Proposta enviada com sucesso! O cliente foi notificado.')
            recarregar()
          }}
        />
      ) : (
        <Alerta tipo="info">Esta necessidade não está mais aberta para propostas.</Alerta>
      )}
      <Visualizador src={arquivo} aoFechar={() => setArquivo(null)} />
    </div>
  )
}

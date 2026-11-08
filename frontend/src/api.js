// Cliente HTTP da API Django REST (autenticação por token).

const BASE = (import.meta.env && import.meta.env.VITE_API_URL) || ''
const CHAVE_TOKEN = 'nf_token'

export const getToken = () => localStorage.getItem(CHAVE_TOKEN)
export const setToken = (t) => (t ? localStorage.setItem(CHAVE_TOKEN, t) : localStorage.removeItem(CHAVE_TOKEN))

export class ApiError extends Error {
  constructor(status, data) {
    super(mensagemDeErro(data) || `Erro ${status}`)
    this.status = status
    this.data = data || {}
  }
  // erros por campo: { campo: 'mensagem' }
  get campos() {
    const out = {}
    for (const [k, v] of Object.entries(this.data || {})) {
      if (k === 'detail' || k === 'non_field_errors') continue
      out[k] = Array.isArray(v) ? v.map(String).join(' ') : typeof v === 'object' ? JSON.stringify(v) : String(v)
    }
    return out
  }
}

function mensagemDeErro(data) {
  if (!data) return ''
  if (typeof data === 'string') return data
  if (data.detail) return Array.isArray(data.detail) ? data.detail.join(' ') : String(data.detail)
  if (data.non_field_errors) return data.non_field_errors.join(' ')
  const primeiro = Object.entries(data)[0]
  if (!primeiro) return ''
  const [campo, msg] = primeiro
  const texto = Array.isArray(msg) ? (typeof msg[0] === 'object' ? 'verifique os itens informados' : msg.join(' ')) : String(msg)
  return `${campo.replace(/_/g, ' ')}: ${texto}`
}

export async function api(caminho, { method = 'GET', body, form } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Token ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(`${BASE}/api${caminho}`, { method, headers, body: payload })
  } catch {
    throw new ApiError(0, { detail: 'Não foi possível conectar à API. O backend (Django) está rodando?' })
  }
  if (res.status === 401 && token) {
    setToken(null)
    window.dispatchEvent(new Event('nf:sessao-expirada'))
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}

// FormData a partir de um objeto (ignora valores vazios / nulos)
export function paraFormData(obj) {
  const fd = new FormData()
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined || v === null || v === '') continue
    fd.append(k, v)
  }
  return fd
}

// ---------------------------------------------------------------- formatação
const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const num = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })

export const moeda = (v) => (v === null || v === undefined || v === '' ? '—' : brl.format(Number(v)))
export const numero = (v) => (v === null || v === undefined || v === '' ? '—' : num.format(Number(v)))
export const dataCurta = (s) => (s ? new Date(s.length === 10 ? `${s}T12:00:00` : s).toLocaleDateString('pt-BR') : '—')
export const dataHora = (s) =>
  s ? new Date(s).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'
export const medidas = (n) => `${numero(n.altura)} × ${numero(n.largura)} × ${numero(n.profundidade)} cm`
export const ehPdf = (url) => typeof url === 'string' && url.toLowerCase().split('?')[0].endsWith('.pdf')

export const AMBIENTES = [
  ['COZINHA', 'Cozinha'],
  ['QUARTO', 'Quarto'],
  ['SALA', 'Sala'],
  ['BANHEIRO', 'Banheiro'],
  ['AREA_EXTERNA', 'Área externa'],
  ['ESCRITORIO', 'Escritório'],
]

export const TIPOS_MATERIAL = [
  ['MDF', 'MDF'],
  ['COMPENSADO', 'Compensado'],
  ['MADEIRA_DE_LEI', 'Madeira de lei'],
  ['ACO', 'Aço'],
  ['FERRAGEM', 'Ferragens e acessórios'],
  ['OUTRO', 'Outro'],
]

export const UNIDADES = [
  ['m2', 'm²'],
  ['m', 'm'],
  ['un', 'un'],
  ['kg', 'kg'],
]

export const VALOR_HORA_REFERENCIA = 60

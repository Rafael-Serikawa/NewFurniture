import { useAuth } from '../auth'
import { Link } from '../router'

const EQUIPE = [
  'Erick Kamada Pesce de Oliveira',
  'Lucas Hideki Toyofuku Turri',
  'Rafael Tadao Mendes Serikawa',
  'Victor Hugo de Ávila Ribeiro',
]

export default function Sobre() {
  const { usuario } = useAuth()
  return (
    <div className="pagina sobre">
      <section className="sobre-hero">
        <h1>Sobre a NewFurniture</h1>
        <p>
          O mercado de móveis planejados é fragmentado: orçamentos caros e demorados, ruído de comunicação, marceneiros com baixa
          produtividade e designers independentes com demanda reprimida. A NewFurniture organiza esse processo em três etapas, em
          uma única plataforma.
        </p>
        {!usuario && (
          <Link para="/cadastro" className="botao">
            Criar conta
          </Link>
        )}
      </section>

      <section className="sobre-etapas">
        <article>
          <span>01</span>
          <h3>Cliente publica a necessidade</h3>
          <p>Informa o ambiente, as medidas (largura, altura e profundidade), fotos e quanto espera gastar.</p>
        </article>
        <article>
          <span>02</span>
          <h3>Designers propõem o desenho</h3>
          <p>Arquitetos e designers enviam desenho técnico, lista de materiais e sua comissão. O cliente aprova e paga.</p>
        </article>
        <article>
          <span>03</span>
          <h3>Marceneiro fabrica o kit</h3>
          <p>Marcenarias concorrem pela execução, fabricam as peças e combinam a entrega. O cliente monta em casa.</p>
        </article>
      </section>

      <section className="sobre-orcamento">
        <h2>Orçamento final transparente</h2>
        <p>
          Cada projeto tem um <b>Orçamento Final</b> que cruza as dimensões do sistema: custo e quantidade de materiais (da proposta
          técnica), horas e valor da mão de obra (da proposta do marceneiro escolhido) e a comissão do designer — com o preço total
          calculado dinamicamente.
        </p>
      </section>

      <section className="sobre-equipe">
        <h2>Equipe</h2>
        <p className="nota">PMR3304 — Sistemas de Informação · Escola Politécnica da USP · 2026</p>
        <ul>
          {EQUIPE.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </section>
    </div>
  )
}

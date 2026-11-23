"""
Totalizações da entidade multidimensional OrcamentoFinal.

Cada orçamento é um "fato" com:
  - dimensões: tipo de ambiente, cidade, estado da OS, mês, designer, marceneiro
  - medidas:   quantidade de projetos, quantidade/custo de materiais, horas e custo
               de mão de obra, comissão do designer e preço total

A dimensão "tipo de material" é mais fina (uma linha por material), então usa
os itens de material como fatos, com as medidas de quantidade e custo.
"""
from collections import OrderedDict
from decimal import Decimal

from django.utils import timezone

from .models import Material, Necessidade, OrdemServico

ZERO = Decimal('0')

DIMENSOES = OrderedDict([
    ('tipo_ambiente', 'Tipo de ambiente'),
    ('cidade', 'Cidade'),
    ('estado', 'Estado da OS'),
    ('mes', 'Mês'),
    ('designer', 'Designer'),
    ('marceneiro', 'Marceneiro'),
    ('tipo_material', 'Tipo de material'),
])

MEDIDAS = OrderedDict([
    ('quantidade_projetos', 'Projetos'),
    ('qtde_materiais', 'Qtde. de materiais'),
    ('custo_materiais', 'Custo de materiais (R$)'),
    ('horas_marceneiro', 'Horas de marcenaria'),
    ('custo_mao_obra', 'Mão de obra (R$)'),
    ('comissao_designer', 'Comissão do designer (R$)'),
    ('preco_total', 'Preço total (R$)'),
])

# medidas disponíveis quando a dimensão "tipo de material" está envolvida
MEDIDAS_MATERIAL = ['quantidade_projetos', 'qtde_materiais', 'custo_materiais']

_AMBIENTES = dict(Necessidade.Ambiente.choices)
_ESTADOS = dict(OrdemServico.Estado.choices)
_MATERIAIS = dict(Material.Tipo.choices)
_MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


def _chave_e_rotulo(dimensao, orcamento, material=None):
    ordem = orcamento.ordem
    necessidade = ordem.proposta_tecnica.necessidade
    if dimensao == 'tipo_ambiente':
        return necessidade.tipo_ambiente, _AMBIENTES.get(necessidade.tipo_ambiente, necessidade.tipo_ambiente)
    if dimensao == 'cidade':
        cidade = (necessidade.cidade or '').strip() or '—'
        return cidade.lower(), cidade.title()
    if dimensao == 'estado':
        return ordem.estado, _ESTADOS.get(ordem.estado, ordem.estado)
    if dimensao == 'mes':
        data = timezone.localtime(ordem.criado_em)
        return data.strftime('%Y-%m'), f'{_MESES[data.month - 1]}/{data.year}'
    if dimensao == 'designer':
        designer = ordem.proposta_tecnica.designer
        return str(designer.pk), designer.nome
    if dimensao == 'marceneiro':
        if ordem.marceneiro_id is None:
            return '0', 'Sem marceneiro'
        return str(ordem.marceneiro_id), ordem.marceneiro.nome
    if dimensao == 'tipo_material' and material is not None:
        return material.tipo_material, _MATERIAIS.get(material.tipo_material, material.tipo_material)
    return 'total', 'Total'


def _fatos(orcamentos, usar_materiais):
    """Gera (orcamento, material, medidas) para cada fato."""
    for orc in orcamentos:
        if usar_materiais:
            for mat in orc.ordem.proposta_tecnica.materiais.all():
                yield orc, mat, {
                    'quantidade_projetos': orc.pk,  # contado como distinto
                    'qtde_materiais': mat.quantidade,
                    'custo_materiais': mat.custo_total,
                }
        else:
            yield orc, None, {
                'quantidade_projetos': orc.pk,
                'qtde_materiais': orc.qtde_materiais,
                'custo_materiais': orc.custo_materiais,
                'horas_marceneiro': orc.horas_marceneiro,
                'custo_mao_obra': orc.custo_mao_obra,
                'comissao_designer': orc.comissao_designer,
                'preco_total': orc.preco_total,
            }


class _Acumulador:
    def __init__(self, medidas):
        self.medidas = medidas
        self.somas = {m: ZERO for m in medidas if m != 'quantidade_projetos'}
        self.projetos = set()

    def adicionar(self, valores):
        for medida, valor in valores.items():
            if medida == 'quantidade_projetos':
                self.projetos.add(valor)
            elif medida in self.somas:
                self.somas[medida] += valor or ZERO

    def resultado(self):
        r = {m: round(float(v), 2) for m, v in self.somas.items()}
        if 'quantidade_projetos' in self.medidas:
            r['quantidade_projetos'] = len(self.projetos)
        return r


_ORDEM_FIXA = {
    'tipo_ambiente': list(_AMBIENTES),
    'estado': list(_ESTADOS),
    'tipo_material': list(_MATERIAIS),
}


def _ordenar(chaves_rotulos, dimensao=None):
    """Ordena pelas opções do sistema (ambiente, estado, material) ou alfabeticamente."""
    fixa = _ORDEM_FIXA.get(dimensao)
    if fixa:
        return sorted(chaves_rotulos.items(),
                      key=lambda kv: (fixa.index(kv[0]) if kv[0] in fixa else len(fixa), kv[0]))
    return sorted(chaves_rotulos.items(), key=lambda kv: kv[1] if dimensao in ('designer', 'marceneiro')
                  else kv[0])


def totalizar(orcamentos, dimensao):
    """Agrupa por uma dimensão e soma todas as medidas (com linha de total)."""
    if dimensao not in DIMENSOES:
        raise ValueError('dimensão inválida')
    usar_materiais = dimensao == 'tipo_material'
    medidas = MEDIDAS_MATERIAL if usar_materiais else list(MEDIDAS)
    grupos, rotulos = {}, {}
    total = _Acumulador(medidas)
    for orc, mat, valores in _fatos(orcamentos, usar_materiais):
        chave, rotulo = _chave_e_rotulo(dimensao, orc, mat)
        rotulos[chave] = rotulo
        grupos.setdefault(chave, _Acumulador(medidas)).adicionar(valores)
        total.adicionar(valores)
    linhas = [{'chave': chave, 'rotulo': rotulo, **grupos[chave].resultado()}
              for chave, rotulo in _ordenar(rotulos, dimensao)]
    return {
        'dimensao': dimensao,
        'dimensao_rotulo': DIMENSOES[dimensao],
        'medidas': [{'chave': m, 'rotulo': MEDIDAS[m]} for m in medidas],
        'linhas': linhas,
        'total': total.resultado(),
    }


def cubo(orcamentos, dim_linhas, dim_colunas, medida):
    """Tabela cruzada (dimensão x dimensão) para uma medida, com totais."""
    if dim_linhas not in DIMENSOES or dim_colunas not in DIMENSOES:
        raise ValueError('dimensão inválida')
    if medida not in MEDIDAS:
        raise ValueError('medida inválida')
    usar_materiais = 'tipo_material' in (dim_linhas, dim_colunas)
    if usar_materiais and medida not in MEDIDAS_MATERIAL:
        raise ValueError('com "tipo de material" use projetos, quantidade ou custo de materiais')

    celulas, tot_linhas, tot_colunas = {}, {}, {}
    rot_linhas, rot_colunas = {}, {}
    total = _Acumulador([medida])
    for orc, mat, valores in _fatos(orcamentos, usar_materiais):
        valores = {medida: valores[medida]}
        kl, rl = _chave_e_rotulo(dim_linhas, orc, mat)
        kc, rc = _chave_e_rotulo(dim_colunas, orc, mat)
        rot_linhas[kl], rot_colunas[kc] = rl, rc
        celulas.setdefault(kl, {}).setdefault(kc, _Acumulador([medida])).adicionar(valores)
        tot_linhas.setdefault(kl, _Acumulador([medida])).adicionar(valores)
        tot_colunas.setdefault(kc, _Acumulador([medida])).adicionar(valores)
        total.adicionar(valores)

    def valor(acc):
        return acc.resultado()[medida]

    return {
        'linhas_dimensao': dim_linhas,
        'colunas_dimensao': dim_colunas,
        'medida': medida,
        'medida_rotulo': MEDIDAS[medida],
        'linhas': [{'chave': k, 'rotulo': r} for k, r in _ordenar(rot_linhas, dim_linhas)],
        'colunas': [{'chave': k, 'rotulo': r} for k, r in _ordenar(rot_colunas, dim_colunas)],
        'celulas': {kl: {kc: valor(acc) for kc, acc in cols.items()} for kl, cols in celulas.items()},
        'total_linhas': {k: valor(acc) for k, acc in tot_linhas.items()},
        'total_colunas': {k: valor(acc) for k, acc in tot_colunas.items()},
        'total_geral': valor(total),
    }

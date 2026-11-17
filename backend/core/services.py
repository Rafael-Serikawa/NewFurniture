"""
Regras de negócio dos casos de uso (camada de serviço).

Cada função corresponde a um caso de uso da especificação v1.3:
  NEC001 cadastro de necessidade ............ (serializer + view)
  DES001 inclusão de desenho técnico ........ submeter_proposta_tecnica
  APR001 aprovar proposta de móvel .......... aprovar_proposta_tecnica
  (DER)  proposta de execução do marceneiro . propor_execucao / escolher_marceneiro
  MAR001 iniciar usinagem / recusar ordem ... iniciar_usinagem / recusar_ordem
  MAR002 finalizar fabricação ............... finalizar_fabricacao
  ENT001 propor método de entrega ........... propor_entrega
  ENT002 avaliar método de entrega .......... avaliar_entrega
  (ext.) confirmar recebimento .............. confirmar_recebimento
"""
import re

from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from .models import (Marceneiro, Necessidade, Notificacao, OrcamentoFinal, OrdemServico, Pagamento,
                     PropostaTecnica)


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------
def notificar(usuarios, mensagem, link=''):
    """Cria notificações para um usuário ou uma lista de usuários."""
    if not isinstance(usuarios, (list, tuple, set)) and not hasattr(usuarios, '__iter__'):
        usuarios = [usuarios]
    Notificacao.objects.bulk_create([
        Notificacao(usuario_id=u.pk, mensagem=mensagem[:255], link=link)
        for u in usuarios if u is not None
    ])


def _link_ordem(ordem):
    return f'/ordens/{ordem.pk}'


def _exigir(condicao, mensagem):
    if not condicao:
        raise ValidationError({'detail': mensagem})


def processar_pagamento(cliente, valor, tipo_servico, dados, **referencias):
    """Simula a operadora de cartão.

    Regras da simulação: qualquer cartão válido é aprovado, exceto os que
    terminam em 0000 (usados para demonstrar o fluxo alternativo de recusa).
    Apenas os 4 últimos dígitos são armazenados.
    """
    dados = dados or {}
    numero = re.sub(r'\D', '', str(dados.get('numero_cartao', '')))
    nome = str(dados.get('nome_titular', '')).strip()
    validade = str(dados.get('validade', '')).strip()
    cvv = re.sub(r'\D', '', str(dados.get('cvv', '')))

    erros = {}
    if not nome:
        erros['nome_titular'] = ['Informe o nome impresso no cartão.']
    if not 13 <= len(numero) <= 19:
        erros['numero_cartao'] = ['Número de cartão inválido.']
    if not re.fullmatch(r'(0[1-9]|1[0-2])/\d{2}', validade):
        erros['validade'] = ['Use o formato MM/AA.']
    if len(cvv) not in (3, 4):
        erros['cvv'] = ['CVV inválido.']
    if erros:
        raise ValidationError(erros)

    status = (Pagamento.Status.RECUSADO if numero.endswith('0000')
              else Pagamento.Status.APROVADO)
    return Pagamento.objects.create(
        cliente_id=cliente.pk, tipo_servico=tipo_servico, valor=valor, status=status,
        nome_titular=nome[:100], cartao_final=numero[-4:], **referencias,
    )


# ---------------------------------------------------------------------------
# DES001 - Inclusão de desenho técnico
# ---------------------------------------------------------------------------
def validar_nova_proposta_tecnica(necessidade, designer):
    _exigir(necessidade.estado == Necessidade.Estado.ABERTA,
            'Esta necessidade não está mais aberta para propostas.')
    _exigir(not necessidade.propostas.filter(designer_id=designer.pk).exists(),
            'Você já enviou uma proposta para esta necessidade.')


def pos_submeter_proposta_tecnica(proposta):
    necessidade = proposta.necessidade
    notificar(necessidade.cliente,
              f'Nova proposta de {proposta.designer.nome} para "{necessidade.titulo}".',
              f'/pedidos/{necessidade.pk}')


# ---------------------------------------------------------------------------
# APR001 - Aprovar proposta de móvel (com pagamento)
# ---------------------------------------------------------------------------
def aprovar_proposta_tecnica(proposta, cliente, dados_pagamento):
    necessidade = proposta.necessidade
    if necessidade.cliente_id != cliente.pk:
        raise NotFound('Proposta não encontrada.')
    _exigir(necessidade.estado == Necessidade.Estado.ABERTA, 'Esta necessidade já foi resolvida.')
    _exigir(proposta.estado == PropostaTecnica.Estado.SUBMETIDA, 'Esta proposta não pode mais ser aprovada.')

    pagamento = processar_pagamento(cliente, proposta.valor_projeto, Pagamento.TipoServico.PROJETO,
                                    dados_pagamento, proposta_tecnica=proposta)
    if pagamento.status != Pagamento.Status.APROVADO:
        return pagamento, None  # fluxo alternativo: pagamento recusado

    with transaction.atomic():
        proposta.estado = PropostaTecnica.Estado.APROVADA
        proposta.save(update_fields=['estado'])
        concorrentes = list(necessidade.propostas.exclude(pk=proposta.pk)
                            .select_related('designer'))
        necessidade.propostas.exclude(pk=proposta.pk).update(estado=PropostaTecnica.Estado.ARQUIVADA)
        necessidade.estado = Necessidade.Estado.RESOLVIDA
        necessidade.save(update_fields=['estado'])

        ordem = OrdemServico.objects.create(proposta_tecnica=proposta)
        OrcamentoFinal.objects.create(ordem=ordem).recalcular()

    link = _link_ordem(ordem)
    notificar(proposta.designer, f'Sua proposta para "{necessidade.titulo}" foi aprovada!', link)
    notificar([p.designer for p in concorrentes],
              f'O cliente escolheu outro projeto para "{necessidade.titulo}". Sua proposta foi arquivada.',
              '/minhas-propostas')
    notificar(list(Marceneiro.objects.all()),
              f'Nova ordem de serviço disponível: "{necessidade.titulo}" ({necessidade.cidade}).', link)
    return pagamento, ordem
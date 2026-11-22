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
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from .models import (Marceneiro, Necessidade, Notificacao, OrcamentoFinal, OrdemServico,
                     Pagamento, PropostaEntrega, PropostaMarcenaria, PropostaTecnica)


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


# ---------------------------------------------------------------------------
# Concorrência na fabricação (Proposta_Marcenaria do DER)
# ---------------------------------------------------------------------------
def propor_execucao(ordem, marceneiro, dados):
    _exigir(ordem.estado == OrdemServico.Estado.PENDENTE and ordem.marceneiro_id is None,
            'Esta ordem de serviço não está recebendo propostas.')
    _exigir(not ordem.propostas_marcenaria.filter(marceneiro_id=marceneiro.pk).exists(),
            'Você já enviou uma proposta para esta ordem de serviço.')
    proposta = PropostaMarcenaria.objects.create(ordem=ordem, marceneiro_id=marceneiro.pk, **dados)
    notificar(ordem.necessidade.cliente,
              f'{marceneiro.nome} enviou uma proposta de execução para "{ordem.necessidade.titulo}".',
              _link_ordem(ordem))
    return proposta


def escolher_marceneiro(ordem, cliente, proposta_id, dados_pagamento):
    if ordem.necessidade.cliente_id != cliente.pk:
        raise NotFound('Ordem de serviço não encontrada.')
    _exigir(ordem.estado == OrdemServico.Estado.PENDENTE and ordem.marceneiro_id is None,
            'Esta ordem de serviço já possui um marceneiro.')
    proposta = ordem.propostas_marcenaria.filter(pk=proposta_id).select_related('marceneiro').first()
    _exigir(proposta is not None, 'Proposta de marcenaria inválida.')
    _exigir(proposta.status == PropostaMarcenaria.Status.SUBMETIDA, 'Esta proposta não está mais disponível.')

    pagamento = processar_pagamento(cliente, proposta.custo_execucao, Pagamento.TipoServico.EXECUCAO,
                                    dados_pagamento, proposta_marcenaria=proposta)
    if pagamento.status != Pagamento.Status.APROVADO:
        return pagamento

    with transaction.atomic():
        proposta.status = PropostaMarcenaria.Status.ACEITA
        proposta.save(update_fields=['status'])
        recusadas = list(ordem.propostas_marcenaria.filter(status=PropostaMarcenaria.Status.SUBMETIDA)
                         .exclude(pk=proposta.pk).select_related('marceneiro'))
        ordem.propostas_marcenaria.filter(status=PropostaMarcenaria.Status.SUBMETIDA) \
            .exclude(pk=proposta.pk).update(status=PropostaMarcenaria.Status.RECUSADA)
        ordem.marceneiro = proposta.marceneiro
        ordem.save(update_fields=['marceneiro'])
        ordem.orcamento.recalcular()

    link = _link_ordem(ordem)
    titulo = ordem.necessidade.titulo
    notificar(proposta.marceneiro, f'Você foi escolhido para fabricar "{titulo}". Inicie a usinagem!', link)
    notificar([p.marceneiro for p in recusadas], f'O cliente escolheu outro marceneiro para "{titulo}".', link)
    return pagamento


# ---------------------------------------------------------------------------
# MAR001 - Iniciar usinagem / recusar ordem
# ---------------------------------------------------------------------------
def _exigir_responsavel(ordem, marceneiro):
    if ordem.marceneiro_id != marceneiro.pk:
        raise NotFound('Ordem de serviço não encontrada entre os seus projetos.')


def iniciar_usinagem(ordem, marceneiro):
    _exigir_responsavel(ordem, marceneiro)
    _exigir(ordem.estado == OrdemServico.Estado.PENDENTE, 'A ordem precisa estar no estado "Pendente".')
    ordem.estado = OrdemServico.Estado.EM_USINAGEM
    ordem.data_inicio = timezone.now()
    ordem.save(update_fields=['estado', 'data_inicio'])
    titulo = ordem.necessidade.titulo
    notificar([ordem.necessidade.cliente, ordem.proposta_tecnica.designer],
              f'A fabricação de "{titulo}" começou (em usinagem).', _link_ordem(ordem))
    return ordem


def recusar_ordem(ordem, marceneiro, motivo):
    _exigir_responsavel(ordem, marceneiro)
    _exigir(ordem.estado == OrdemServico.Estado.PENDENTE, 'Só é possível recusar ordens pendentes.')
    motivo = (motivo or '').strip()
    _exigir(motivo, 'Informe o motivo da recusa.')
    with transaction.atomic():
        aceita = ordem.propostas_marcenaria.filter(status=PropostaMarcenaria.Status.ACEITA).first()
        if aceita:
            aceita.status = PropostaMarcenaria.Status.RECUSADA
            aceita.save(update_fields=['status'])
            aceita.pagamentos.filter(status=Pagamento.Status.APROVADO) \
                .update(status=Pagamento.Status.REEMBOLSADO)
        ordem.estado = OrdemServico.Estado.CANCELADA
        ordem.motivo_recusa = motivo
        ordem.save(update_fields=['estado', 'motivo_recusa'])
        ordem.orcamento.recalcular()
    titulo = ordem.necessidade.titulo
    notificar([ordem.necessidade.cliente, ordem.proposta_tecnica.designer],
              f'{marceneiro.nome} recusou a ordem de "{titulo}". O pagamento da execução foi reembolsado.',
              _link_ordem(ordem))
    return ordem


def redirecionar_ordem(ordem, cliente):
    """Após uma recusa, reabre a OS para outras marcenarias sem perder o projeto."""
    if ordem.necessidade.cliente_id != cliente.pk:
        raise NotFound('Ordem de serviço não encontrada.')
    _exigir(ordem.estado == OrdemServico.Estado.CANCELADA, 'Só é possível redirecionar ordens canceladas.')
    recusou = ordem.marceneiro_id
    ordem.estado = OrdemServico.Estado.PENDENTE
    ordem.marceneiro = None
    ordem.save(update_fields=['estado', 'marceneiro'])
    ordem.orcamento.recalcular()
    notificar(list(Marceneiro.objects.exclude(pk=recusou)),
              f'Ordem de serviço disponível novamente: "{ordem.necessidade.titulo}".', _link_ordem(ordem))
    return ordem


# ---------------------------------------------------------------------------
# MAR002 - Finalizar fabricação
# ---------------------------------------------------------------------------
def finalizar_fabricacao(ordem, marceneiro):
    _exigir_responsavel(ordem, marceneiro)
    _exigir(ordem.estado == OrdemServico.Estado.EM_USINAGEM, 'A ordem precisa estar "Em usinagem".')
    ordem.estado = OrdemServico.Estado.FINALIZADA
    ordem.data_conclusao = timezone.now()
    ordem.save(update_fields=['estado', 'data_conclusao'])
    notificar(ordem.necessidade.cliente,
              f'O kit de "{ordem.necessidade.titulo}" está pronto para a etapa de logística.',
              _link_ordem(ordem))
    return ordem


# ---------------------------------------------------------------------------
# ENT001 / ENT002 - Método de entrega
# ---------------------------------------------------------------------------
def propor_entrega(ordem, marceneiro, dados):
    _exigir_responsavel(ordem, marceneiro)
    _exigir(ordem.estado == OrdemServico.Estado.FINALIZADA,
            'A entrega só pode ser proposta após a fabricação ser finalizada.')
    _exigir(not ordem.propostas_entrega.filter(estado=PropostaEntrega.Estado.AGUARDANDO).exists(),
            'Já existe uma proposta de entrega aguardando a avaliação do cliente.')
    proposta = PropostaEntrega.objects.create(ordem=ordem, **dados)
    notificar(ordem.necessidade.cliente,
              f'Proposta de entrega para "{ordem.necessidade.titulo}" aguardando sua avaliação.',
              _link_ordem(ordem))
    return proposta


def avaliar_entrega(ordem, cliente, acao, justificativa=''):
    if ordem.necessidade.cliente_id != cliente.pk:
        raise NotFound('Ordem de serviço não encontrada.')
    _exigir(ordem.estado == OrdemServico.Estado.FINALIZADA, 'Não há entrega para avaliar nesta ordem.')
    proposta = ordem.propostas_entrega.filter(estado=PropostaEntrega.Estado.AGUARDANDO).last()
    _exigir(proposta is not None, 'Não há proposta de entrega aguardando avaliação.')
    titulo = ordem.necessidade.titulo

    if acao == 'aprovar':
        with transaction.atomic():
            proposta.estado = PropostaEntrega.Estado.APROVADA
            proposta.save(update_fields=['estado'])
            ordem.estado = OrdemServico.Estado.ENTREGA_ACORDADA
            ordem.save(update_fields=['estado'])
        notificar(ordem.marceneiro, f'O cliente aprovou a entrega de "{titulo}".', _link_ordem(ordem))
    elif acao == 'alterar':
        justificativa = (justificativa or '').strip()
        _exigir(justificativa, 'Escreva a justificativa ou contraproposta.')
        proposta.estado = PropostaEntrega.Estado.ALTERACAO_SOLICITADA
        proposta.justificativa_cliente = justificativa[:700]
        proposta.save(update_fields=['estado', 'justificativa_cliente'])
        notificar(ordem.marceneiro, f'O cliente pediu alteração na entrega de "{titulo}".',
                  _link_ordem(ordem))
    else:
        raise ValidationError({'acao': ['Use "aprovar" ou "alterar".']})
    return proposta


def confirmar_recebimento(ordem, cliente):
    if ordem.necessidade.cliente_id != cliente.pk:
        raise NotFound('Ordem de serviço não encontrada.')
    _exigir(ordem.estado == OrdemServico.Estado.ENTREGA_ACORDADA,
            'O recebimento só pode ser confirmado após a entrega ser acordada.')
    ordem.estado = OrdemServico.Estado.ENTREGUE
    ordem.save(update_fields=['estado'])
    notificar([ordem.marceneiro, ordem.proposta_tecnica.designer],
              f'Projeto "{ordem.necessidade.titulo}" concluído e entregue ao cliente!', _link_ordem(ordem))
    return ordem

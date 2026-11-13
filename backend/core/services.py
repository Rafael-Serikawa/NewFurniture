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

from rest_framework.exceptions import ValidationError

from .models import Notificacao


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
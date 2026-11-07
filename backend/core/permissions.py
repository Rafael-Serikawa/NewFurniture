"""Controle de acesso por perfil (tipo de usuário)."""
from rest_framework.permissions import BasePermission

from .models import Usuario


class _PorTipo(BasePermission):
    tipo = None
    message = 'Ação não permitida para o seu perfil.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.tipo == self.tipo)


class EhCliente(_PorTipo):
    tipo = Usuario.Tipo.CLIENTE
    message = 'Apenas clientes podem realizar esta ação.'


class EhDesigner(_PorTipo):
    tipo = Usuario.Tipo.DESIGNER
    message = 'Apenas designers podem realizar esta ação.'


class EhMarceneiro(_PorTipo):
    tipo = Usuario.Tipo.MARCENEIRO
    message = 'Apenas marceneiros podem realizar esta ação.'

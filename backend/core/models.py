"""
Modelos do NewFurniture — implementação do Diagrama Entidade Relação.

Generalização/especialização:  Usuario  ->  Cliente | Designer | Marceneiro
Relação 1 x n:                 Cliente  publica  N Necessidades
Relação n x n (Designer x Necessidade):  entidade associativa PropostaTecnica
Relação n x n (Marceneiro x OrdemServico): entidade associativa PropostaMarcenaria
Entidade multidimensional:     OrcamentoFinal (1:1 com OrdemServico)
"""
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

IMAGEM = FileExtensionValidator(['jpg', 'jpeg', 'png'])
IMAGEM_OU_PDF = FileExtensionValidator(['jpg', 'jpeg', 'png', 'pdf'])

# Valor-hora de referência usado para estimar a mão de obra antes de um
# marceneiro ser escolhido.
VALOR_HORA_REFERENCIA = Decimal('60.00')
ZERO = Decimal('0')


# ---------------------------------------------------------------------------
# Usuários (superentidade + especializações)
# ---------------------------------------------------------------------------
class Usuario(AbstractUser):
    class Tipo(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente'
        DESIGNER = 'DESIGNER', 'Designer'
        MARCENEIRO = 'MARCENEIRO', 'Marceneiro'

    nome = models.CharField(max_length=150)
    email = models.EmailField('e-mail', unique=True)
    tipo = models.CharField('tipo de usuário', max_length=20, choices=Tipo.choices, blank=True)
    cidade = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return f'{self.nome or self.username} ({self.get_tipo_display() or "admin"})'


class Cliente(Usuario):
    """Especialização: quem publica necessidades e paga pelo projeto."""

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'


class Designer(Usuario):
    """Especialização: arquiteto/designer que envia propostas técnicas."""
    especialidade = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'designer'
        verbose_name_plural = 'designers'


class Marceneiro(Usuario):
    """Especialização: fabrica as peças."""
    valor_hora = models.DecimalField(
        'valor da hora (R$)', max_digits=8, decimal_places=2, default=VALOR_HORA_REFERENCIA,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        verbose_name = 'marceneiro'
        verbose_name_plural = 'marceneiros'

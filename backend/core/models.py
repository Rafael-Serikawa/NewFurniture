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


# ---------------------------------------------------------------------------
# Fase de ideias
# ---------------------------------------------------------------------------
class Necessidade(models.Model):
    class Ambiente(models.TextChoices):
        COZINHA = 'COZINHA', 'Cozinha'
        QUARTO = 'QUARTO', 'Quarto'
        SALA = 'SALA', 'Sala'
        BANHEIRO = 'BANHEIRO', 'Banheiro'
        AREA_EXTERNA = 'AREA_EXTERNA', 'Área externa'
        ESCRITORIO = 'ESCRITORIO', 'Escritório'

    class Estado(models.TextChoices):
        ABERTA = 'ABERTA', 'Aberta'
        RESOLVIDA = 'RESOLVIDA', 'Resolvida'

    codigo = models.CharField('código', max_length=8, unique=True, null=True, blank=True, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='necessidades')
    titulo = models.CharField('título do projeto', max_length=100)
    cidade = models.CharField(max_length=100)
    tipo_ambiente = models.CharField('tipo de ambiente', max_length=20, choices=Ambiente.choices)
    largura = models.DecimalField('largura (cm)', max_digits=7, decimal_places=1,
                                  validators=[MinValueValidator(Decimal('0.1'))])
    altura = models.DecimalField('altura (cm)', max_digits=7, decimal_places=1,
                                 validators=[MinValueValidator(Decimal('0.1'))])
    profundidade = models.DecimalField('profundidade (cm)', max_digits=7, decimal_places=1,
                                       validators=[MinValueValidator(Decimal('0.1'))])
    foto_ambiente = models.FileField('foto do ambiente', upload_to='necessidades/fotos/',
                                     max_length=255, validators=[IMAGEM])
    esboco_movel = models.FileField('esboço do móvel', upload_to='necessidades/esbocos/',
                                    max_length=255, validators=[IMAGEM_OU_PDF], blank=True)
    observacoes = models.TextField('observações adicionais', max_length=700, blank=True)
    custo_esperado = models.PositiveIntegerField('custo esperado (R$)')
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABERTA)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em', '-id']
        verbose_name = 'necessidade'
        verbose_name_plural = 'necessidades'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo:
            # código sequencial com 8 dígitos (NEC001, passo 7)
            self.codigo = f'{self.pk:08d}'
            Necessidade.objects.filter(pk=self.pk).update(codigo=self.codigo)

    def __str__(self):
        return f'{self.codigo} - {self.titulo}'


class PropostaTecnica(models.Model):
    """Entidade associativa que resolve a relação n x n Designer x Necessidade."""

    class Estado(models.TextChoices):
        SUBMETIDA = 'SUBMETIDA', 'Submetida'
        APROVADA = 'APROVADA', 'Aprovada'
        ARQUIVADA = 'ARQUIVADA', 'Arquivada'

    necessidade = models.ForeignKey(Necessidade, on_delete=models.CASCADE, related_name='propostas')
    designer = models.ForeignKey(Designer, on_delete=models.CASCADE, related_name='propostas')
    desenho_tecnico = models.FileField('desenho técnico', upload_to='propostas/desenhos/',
                                       max_length=255, validators=[IMAGEM_OU_PDF])
    descricao = models.TextField('descrição / observações', max_length=1000, blank=True)
    comissao_designer = models.DecimalField('comissão do designer (R$)', max_digits=10, decimal_places=2,
                                            validators=[MinValueValidator(ZERO)])
    horas_estimadas = models.DecimalField('horas de marcenaria estimadas', max_digits=7, decimal_places=1,
                                          default=ZERO, validators=[MinValueValidator(ZERO)])
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.SUBMETIDA)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em', '-id']
        verbose_name = 'proposta técnica'
        verbose_name_plural = 'propostas técnicas'

    def __str__(self):
        return f'Proposta #{self.pk} de {self.designer.nome} para {self.necessidade}'

    # --- totalizações da proposta ---
    @property
    def quantidade_material(self):
        return sum((m.quantidade for m in self.materiais.all()), ZERO)

    @property
    def custo_materiais(self):
        return sum((m.custo_total for m in self.materiais.all()), ZERO)

    @property
    def estimativa_mao_obra(self):
        return self.horas_estimadas * VALOR_HORA_REFERENCIA

    @property
    def valor_projeto(self):
        """Valor cobrado na aprovação (APR001): materiais + comissão do designer."""
        return self.custo_materiais + self.comissao_designer

    @property
    def custo_estimado(self):
        """Estimativa completa: materiais + comissão + mão de obra estimada."""
        return self.valor_projeto + self.estimativa_mao_obra


class Material(models.Model):
    class Tipo(models.TextChoices):
        MDF = 'MDF', 'MDF'
        COMPENSADO = 'COMPENSADO', 'Compensado'
        MADEIRA_DE_LEI = 'MADEIRA_DE_LEI', 'Madeira de lei'
        ACO = 'ACO', 'Aço'
        FERRAGEM = 'FERRAGEM', 'Ferragens e acessórios'
        OUTRO = 'OUTRO', 'Outro'

    class Unidade(models.TextChoices):
        M2 = 'm2', 'm²'
        M = 'm', 'm'
        UN = 'un', 'un'
        KG = 'kg', 'kg'

    proposta = models.ForeignKey(PropostaTecnica, on_delete=models.CASCADE, related_name='materiais')
    tipo_material = models.CharField('tipo de material', max_length=20, choices=Tipo.choices)
    descricao = models.CharField('descrição', max_length=120)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.01'))])
    unidade = models.CharField(max_length=5, choices=Unidade.choices, default=Unidade.UN)
    custo_unitario = models.DecimalField('custo unitário (R$)', max_digits=10, decimal_places=2,
                                         validators=[MinValueValidator(ZERO)])

    class Meta:
        ordering = ['id']
        verbose_name = 'material'
        verbose_name_plural = 'materiais'

    @property
    def custo_total(self):
        return self.quantidade * self.custo_unitario

    def __str__(self):
        return f'{self.descricao} ({self.quantidade} {self.unidade})'


# ---------------------------------------------------------------------------
# Fabricação e logística
# ---------------------------------------------------------------------------
class OrdemServico(models.Model):
    class Estado(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        EM_USINAGEM = 'EM_USINAGEM', 'Em usinagem'
        FINALIZADA = 'FINALIZADA', 'Finalizada'
        ENTREGA_ACORDADA = 'ENTREGA_ACORDADA', 'Entrega acordada'
        ENTREGUE = 'ENTREGUE', 'Entregue'
        CANCELADA = 'CANCELADA', 'Cancelada'

    proposta_tecnica = models.OneToOneField(PropostaTecnica, on_delete=models.CASCADE,
                                            related_name='ordem_servico')
    marceneiro = models.ForeignKey(Marceneiro, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='ordens')
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDENTE)
    motivo_recusa = models.TextField('motivo da recusa', blank=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em', '-id']
        verbose_name = 'ordem de serviço'
        verbose_name_plural = 'ordens de serviço'

    @property
    def necessidade(self):
        return self.proposta_tecnica.necessidade

    def __str__(self):
        return f'OS #{self.pk} - {self.necessidade.titulo}'


class PropostaMarcenaria(models.Model):
    """Entidade associativa que resolve a relação n x n Marceneiro x OrdemServico."""

    class Status(models.TextChoices):
        SUBMETIDA = 'SUBMETIDA', 'Submetida'
        ACEITA = 'ACEITA', 'Aceita'
        RECUSADA = 'RECUSADA', 'Recusada'

    ordem = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='propostas_marcenaria')
    marceneiro = models.ForeignKey(Marceneiro, on_delete=models.CASCADE, related_name='propostas_marcenaria')
    horas_trabalho = models.DecimalField('horas de trabalho', max_digits=7, decimal_places=1,
                                         validators=[MinValueValidator(Decimal('0.5'))])
    valor_hora = models.DecimalField('valor da hora (R$)', max_digits=8, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.01'))])
    prazo_estimado_dias = models.PositiveIntegerField('prazo estimado (dias)',
                                                      validators=[MinValueValidator(1)])
    descricao = models.TextField('descrição', max_length=700, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUBMETIDA)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em', 'id']
        verbose_name = 'proposta de marcenaria'
        verbose_name_plural = 'propostas de marcenaria'

    @property
    def custo_execucao(self):
        return self.horas_trabalho * self.valor_hora

    def __str__(self):
        return f'Proposta de {self.marceneiro.nome} para OS #{self.ordem_id}'


class PropostaEntrega(models.Model):
    """Método de entrega proposto pelo marceneiro (composição com a OS)."""

    class Modalidade(models.TextChoices):
        DELIVERY = 'DELIVERY', 'Delivery'
        RETIRADA = 'RETIRADA', 'Retirada'

    class Estado(models.TextChoices):
        AGUARDANDO = 'AGUARDANDO', 'Aguardando avaliação'
        APROVADA = 'APROVADA', 'Aprovada'
        ALTERACAO_SOLICITADA = 'ALTERACAO_SOLICITADA', 'Alteração solicitada'

    ordem = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='propostas_entrega')
    modalidade = models.CharField(max_length=10, choices=Modalidade.choices)
    local = models.CharField(max_length=200)
    prazo = models.DateField('data prevista')
    horarios_disponiveis = models.CharField('horários disponíveis', max_length=200)
    instrucoes = models.TextField('instruções adicionais', max_length=700, blank=True)
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.AGUARDANDO)
    justificativa_cliente = models.TextField(max_length=700, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em', 'id']
        verbose_name = 'proposta de entrega'
        verbose_name_plural = 'propostas de entrega'


# ---------------------------------------------------------------------------
# Face financeira
# ---------------------------------------------------------------------------
class Pagamento(models.Model):
    class TipoServico(models.TextChoices):
        PROJETO = 'PROJETO', 'Projeto (materiais + designer)'
        EXECUCAO = 'EXECUCAO', 'Execução (marcenaria)'

    class Status(models.TextChoices):
        AGUARDANDO = 'AGUARDANDO', 'Aguardando'
        APROVADO = 'APROVADO', 'Aprovado'
        RECUSADO = 'RECUSADO', 'Recusado'
        REEMBOLSADO = 'REEMBOLSADO', 'Reembolsado'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pagamentos')
    tipo_servico = models.CharField(max_length=10, choices=TipoServico.choices)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.AGUARDANDO)
    proposta_tecnica = models.ForeignKey(PropostaTecnica, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='pagamentos')
    proposta_marcenaria = models.ForeignKey(PropostaMarcenaria, on_delete=models.SET_NULL, null=True,
                                            blank=True, related_name='pagamentos')
    nome_titular = models.CharField(max_length=100, blank=True)
    cartao_final = models.CharField('final do cartão', max_length=4, blank=True)
    data_transacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_transacao', '-id']
        verbose_name = 'pagamento'
        verbose_name_plural = 'pagamentos'


class OrcamentoFinal(models.Model):
    """Entidade multidimensional: consolida materiais, mão de obra e comissão."""
    ordem = models.OneToOneField(OrdemServico, on_delete=models.CASCADE, related_name='orcamento')
    qtde_materiais = models.DecimalField(max_digits=12, decimal_places=2, default=ZERO)
    custo_materiais = models.DecimalField(max_digits=12, decimal_places=2, default=ZERO)
    horas_marceneiro = models.DecimalField(max_digits=8, decimal_places=1, default=ZERO)
    valor_hora = models.DecimalField(max_digits=8, decimal_places=2, default=ZERO)
    custo_mao_obra = models.DecimalField(max_digits=12, decimal_places=2, default=ZERO)
    comissao_designer = models.DecimalField(max_digits=12, decimal_places=2, default=ZERO)
    preco_total = models.DecimalField(max_digits=12, decimal_places=2, default=ZERO)
    mao_obra_confirmada = models.BooleanField(default=False)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'orçamento final'
        verbose_name_plural = 'orçamentos finais'

    def recalcular(self):
        """Cruza as dimensões e recalcula o preço total dinamicamente."""
        proposta = self.ordem.proposta_tecnica
        materiais = list(proposta.materiais.all())
        self.qtde_materiais = sum((m.quantidade for m in materiais), ZERO)
        self.custo_materiais = sum((m.custo_total for m in materiais), ZERO)
        self.comissao_designer = proposta.comissao_designer

        escolhida = self.ordem.propostas_marcenaria.filter(
            status=PropostaMarcenaria.Status.ACEITA).first()
        if escolhida:
            self.horas_marceneiro = escolhida.horas_trabalho
            self.valor_hora = escolhida.valor_hora
            self.mao_obra_confirmada = True
        else:
            self.horas_marceneiro = proposta.horas_estimadas
            self.valor_hora = VALOR_HORA_REFERENCIA
            self.mao_obra_confirmada = False
        self.custo_mao_obra = self.horas_marceneiro * self.valor_hora
        self.preco_total = self.custo_materiais + self.custo_mao_obra + self.comissao_designer
        self.save()
        return self

    def __str__(self):
        return f'Orçamento da OS #{self.ordem_id}: R$ {self.preco_total}'


class Notificacao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificacoes')
    mensagem = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    lida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em', '-id']
        verbose_name = 'notificação'
        verbose_name_plural = 'notificações'

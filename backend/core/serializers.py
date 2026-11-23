from django.db.models import Q
from rest_framework import serializers

from .models import (Marceneiro, Material, Necessidade, Notificacao, OrcamentoFinal, OrdemServico, Pagamento,
                     PropostaEntrega, PropostaMarcenaria, PropostaTecnica, Usuario)


def _dinheiro(**kwargs):
    return serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, **kwargs)


def _usuario_logado(serializer):
    request = serializer.context.get('request')
    return getattr(request, 'user', None)


# ---------------------------------------------------------------------------
# Usuários / autenticação
# ---------------------------------------------------------------------------
class UsuarioSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    valor_hora = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email', 'tipo', 'tipo_display', 'cidade', 'valor_hora']

    def get_valor_hora(self, obj):
        if obj.tipo != Usuario.Tipo.MARCENEIRO:
            return None
        if hasattr(obj, 'valor_hora'):  # já é uma instância de Marceneiro
            return float(obj.valor_hora)
        marceneiro = Marceneiro.objects.filter(pk=obj.pk).first()
        return float(marceneiro.valor_hora) if marceneiro else None


class RegistroSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    senha = serializers.CharField(min_length=6, write_only=True)
    tipo = serializers.ChoiceField(choices=Usuario.Tipo.choices)
    cidade = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if Usuario.objects.filter(email__iexact=value).exists() or \
                Usuario.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Já existe uma conta com este e-mail.')
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    senha = serializers.CharField(write_only=True)


# ---------------------------------------------------------------------------
# Necessidade (NEC001)
# ---------------------------------------------------------------------------
class NecessidadeSerializer(serializers.ModelSerializer):
    tipo_ambiente_display = serializers.CharField(source='get_tipo_ambiente_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    total_propostas = serializers.SerializerMethodField()
    propostas_submetidas = serializers.SerializerMethodField()
    ja_propus = serializers.SerializerMethodField()
    ordem_id = serializers.SerializerMethodField()
    ordem_estado = serializers.SerializerMethodField()

    class Meta:
        model = Necessidade
        fields = ['id', 'codigo', 'titulo', 'cidade', 'tipo_ambiente', 'tipo_ambiente_display',
                  'largura', 'altura', 'profundidade', 'foto_ambiente', 'esboco_movel',
                  'observacoes', 'custo_esperado', 'estado', 'estado_display', 'criado_em',
                  'cliente_nome', 'total_propostas', 'propostas_submetidas', 'ja_propus',
                  'ordem_id', 'ordem_estado']
        read_only_fields = ['codigo', 'estado', 'criado_em']

    def get_total_propostas(self, obj):
        return obj.propostas.count()

    def get_propostas_submetidas(self, obj):
        return obj.propostas.filter(estado=PropostaTecnica.Estado.SUBMETIDA).count()

    def get_ja_propus(self, obj):
        user = _usuario_logado(self)
        if not user or user.tipo != Usuario.Tipo.DESIGNER:
            return False
        return obj.propostas.filter(designer_id=user.pk).exists()

    def _ordem(self, obj):
        return OrdemServico.objects.filter(proposta_tecnica__necessidade=obj).first()

    def get_ordem_id(self, obj):
        ordem = self._ordem(obj)
        return ordem.pk if ordem else None

    def get_ordem_estado(self, obj):
        ordem = self._ordem(obj)
        return ordem.estado if ordem else None


class NecessidadeResumoSerializer(serializers.ModelSerializer):
    tipo_ambiente_display = serializers.CharField(source='get_tipo_ambiente_display', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)

    class Meta:
        model = Necessidade
        fields = ['id', 'codigo', 'titulo', 'cidade', 'tipo_ambiente', 'tipo_ambiente_display',
                  'largura', 'altura', 'profundidade', 'foto_ambiente', 'esboco_movel',
                  'observacoes', 'custo_esperado', 'estado', 'cliente_nome']


# ---------------------------------------------------------------------------
# Proposta técnica + materiais (DES001 / APR001)
# ---------------------------------------------------------------------------
class MaterialSerializer(serializers.ModelSerializer):
    tipo_material_display = serializers.CharField(source='get_tipo_material_display', read_only=True)
    unidade_display = serializers.CharField(source='get_unidade_display', read_only=True)
    custo_total = _dinheiro()

    class Meta:
        model = Material
        fields = ['id', 'tipo_material', 'tipo_material_display', 'descricao', 'quantidade',
                  'unidade', 'unidade_display', 'custo_unitario', 'custo_total']


class PropostaTecnicaSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    designer_id = serializers.IntegerField(read_only=True)
    designer_nome = serializers.CharField(source='designer.nome', read_only=True)
    necessidade_titulo = serializers.CharField(source='necessidade.titulo', read_only=True)
    necessidade_codigo = serializers.CharField(source='necessidade.codigo', read_only=True)
    materiais = MaterialSerializer(many=True, read_only=True)
    quantidade_material = _dinheiro()
    custo_materiais = _dinheiro()
    estimativa_mao_obra = _dinheiro()
    valor_projeto = _dinheiro()
    custo_estimado = _dinheiro()
    ordem_id = serializers.SerializerMethodField()

    class Meta:
        model = PropostaTecnica
        fields = ['id', 'necessidade', 'necessidade_titulo', 'necessidade_codigo', 'designer_id',
                  'designer_nome', 'desenho_tecnico', 'descricao', 'comissao_designer',
                  'horas_estimadas', 'estado', 'estado_display', 'materiais', 'quantidade_material',
                  'custo_materiais', 'estimativa_mao_obra', 'valor_projeto', 'custo_estimado',
                  'criado_em', 'ordem_id']
        read_only_fields = ['estado', 'criado_em']

    def get_ordem_id(self, obj):
        ordem = OrdemServico.objects.filter(proposta_tecnica=obj).first()
        return ordem.pk if ordem else None


class NecessidadeDetalheSerializer(NecessidadeSerializer):
    """Detalhe da necessidade com as propostas recebidas.

    O cliente dono vê todas as propostas; um designer vê apenas a própria.
    """
    propostas = serializers.SerializerMethodField()

    class Meta(NecessidadeSerializer.Meta):
        fields = NecessidadeSerializer.Meta.fields + ['propostas']

    def get_propostas(self, obj):
        user = _usuario_logado(self)
        qs = obj.propostas.select_related('designer').prefetch_related('materiais')
        if user and user.tipo == Usuario.Tipo.DESIGNER:
            qs = qs.filter(designer_id=user.pk)
        elif not (user and (user.is_staff or obj.cliente_id == user.pk)):
            qs = qs.none()
        return PropostaTecnicaSerializer(qs, many=True, context=self.context).data


# ---------------------------------------------------------------------------
# Pagamento
# ---------------------------------------------------------------------------
class PagamentoSerializer(serializers.ModelSerializer):
    tipo_servico_display = serializers.CharField(source='get_tipo_servico_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Pagamento
        fields = ['id', 'tipo_servico', 'tipo_servico_display', 'valor', 'status', 'status_display',
                  'nome_titular', 'cartao_final', 'data_transacao']


class DadosPagamentoSerializer(serializers.Serializer):
    nome_titular = serializers.CharField(max_length=100)
    numero_cartao = serializers.CharField(max_length=25)
    validade = serializers.CharField(max_length=5)
    cvv = serializers.CharField(max_length=4)


# ---------------------------------------------------------------------------
# Ordem de serviço, propostas de marcenaria e de entrega
# ---------------------------------------------------------------------------
class PropostaMarcenariaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    marceneiro_id = serializers.IntegerField(read_only=True)
    marceneiro_nome = serializers.CharField(source='marceneiro.nome', read_only=True)
    marceneiro_cidade = serializers.CharField(source='marceneiro.cidade', read_only=True)
    custo_execucao = _dinheiro()

    class Meta:
        model = PropostaMarcenaria
        fields = ['id', 'marceneiro_id', 'marceneiro_nome', 'marceneiro_cidade', 'horas_trabalho',
                  'valor_hora', 'prazo_estimado_dias', 'descricao', 'status', 'status_display',
                  'custo_execucao', 'criado_em']
        read_only_fields = ['status', 'criado_em']


class PropostaEntregaSerializer(serializers.ModelSerializer):
    modalidade_display = serializers.CharField(source='get_modalidade_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = PropostaEntrega
        fields = ['id', 'modalidade', 'modalidade_display', 'local', 'prazo', 'horarios_disponiveis',
                  'instrucoes', 'estado', 'estado_display', 'justificativa_cliente', 'criado_em']
        read_only_fields = ['estado', 'justificativa_cliente', 'criado_em']


class OrcamentoResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrcamentoFinal
        fields = ['id', 'qtde_materiais', 'custo_materiais', 'horas_marceneiro', 'valor_hora',
                  'custo_mao_obra', 'comissao_designer', 'preco_total', 'mao_obra_confirmada',
                  'atualizado_em']


class OrdemServicoSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    necessidade = NecessidadeResumoSerializer(source='proposta_tecnica.necessidade', read_only=True)
    designer_nome = serializers.CharField(source='proposta_tecnica.designer.nome', read_only=True)
    marceneiro_id = serializers.IntegerField(read_only=True)
    marceneiro_nome = serializers.CharField(source='marceneiro.nome', read_only=True, default=None)
    preco_total = serializers.SerializerMethodField()
    orcamento_id = serializers.SerializerMethodField()
    total_propostas_marcenaria = serializers.SerializerMethodField()
    minha_proposta_status = serializers.SerializerMethodField()
    entrega_aguardando = serializers.SerializerMethodField()

    class Meta:
        model = OrdemServico
        fields = ['id', 'estado', 'estado_display', 'necessidade', 'designer_nome', 'marceneiro_id',
                  'marceneiro_nome', 'motivo_recusa', 'data_inicio', 'data_conclusao', 'criado_em',
                  'preco_total', 'orcamento_id', 'total_propostas_marcenaria',
                  'minha_proposta_status', 'entrega_aguardando']

    def _orcamento(self, obj):
        return OrcamentoFinal.objects.filter(ordem=obj).first()

    def get_preco_total(self, obj):
        orc = self._orcamento(obj)
        return float(orc.preco_total) if orc else None

    def get_orcamento_id(self, obj):
        orc = self._orcamento(obj)
        return orc.pk if orc else None

    def get_total_propostas_marcenaria(self, obj):
        return obj.propostas_marcenaria.count()

    def get_minha_proposta_status(self, obj):
        user = _usuario_logado(self)
        if not user or user.tipo != Usuario.Tipo.MARCENEIRO:
            return None
        proposta = obj.propostas_marcenaria.filter(marceneiro_id=user.pk).first()
        return proposta.status if proposta else None

    def get_entrega_aguardando(self, obj):
        return obj.propostas_entrega.filter(estado=PropostaEntrega.Estado.AGUARDANDO).exists()


class OrdemServicoDetalheSerializer(OrdemServicoSerializer):
    proposta_tecnica = PropostaTecnicaSerializer(read_only=True)
    propostas_marcenaria = serializers.SerializerMethodField()
    propostas_entrega = PropostaEntregaSerializer(many=True, read_only=True)
    orcamento = serializers.SerializerMethodField()
    pagamentos = serializers.SerializerMethodField()

    class Meta(OrdemServicoSerializer.Meta):
        fields = OrdemServicoSerializer.Meta.fields + [
            'proposta_tecnica', 'propostas_marcenaria', 'propostas_entrega', 'orcamento', 'pagamentos']

    def get_propostas_marcenaria(self, obj):
        user = _usuario_logado(self)
        qs = obj.propostas_marcenaria.select_related('marceneiro')
        eh_cliente = user and obj.necessidade.cliente_id == user.pk
        if user and user.tipo == Usuario.Tipo.MARCENEIRO:
            qs = qs.filter(marceneiro_id=user.pk)
        elif not (eh_cliente or (user and user.is_staff)):
            qs = qs.filter(status=PropostaMarcenaria.Status.ACEITA)
        return PropostaMarcenariaSerializer(qs, many=True, context=self.context).data

    def get_orcamento(self, obj):
        orc = self._orcamento(obj)
        return OrcamentoResumoSerializer(orc).data if orc else None

    def get_pagamentos(self, obj):
        user = _usuario_logado(self)
        if not user or not (user.is_staff or obj.necessidade.cliente_id == user.pk):
            return []
        qs = Pagamento.objects.filter(
            Q(proposta_tecnica=obj.proposta_tecnica) | Q(proposta_marcenaria__ordem=obj))
        return PagamentoSerializer(qs.order_by('data_transacao', 'id'), many=True).data


# ---------------------------------------------------------------------------
# Orçamento final (entidade multidimensional)
# ---------------------------------------------------------------------------
class OrcamentoFinalSerializer(serializers.ModelSerializer):
    ordem_id = serializers.IntegerField(read_only=True)
    ordem_estado = serializers.CharField(source='ordem.estado', read_only=True)
    ordem_estado_display = serializers.CharField(source='ordem.get_estado_display', read_only=True)
    titulo = serializers.CharField(source='ordem.proposta_tecnica.necessidade.titulo', read_only=True)
    codigo = serializers.CharField(source='ordem.proposta_tecnica.necessidade.codigo', read_only=True)
    tipo_ambiente = serializers.CharField(source='ordem.proposta_tecnica.necessidade.tipo_ambiente',
                                          read_only=True)
    tipo_ambiente_display = serializers.CharField(
        source='ordem.proposta_tecnica.necessidade.get_tipo_ambiente_display', read_only=True)
    cidade = serializers.CharField(source='ordem.proposta_tecnica.necessidade.cidade', read_only=True)
    cliente_nome = serializers.CharField(source='ordem.proposta_tecnica.necessidade.cliente.nome',
                                         read_only=True)
    designer_nome = serializers.CharField(source='ordem.proposta_tecnica.designer.nome', read_only=True)
    marceneiro_nome = serializers.CharField(source='ordem.marceneiro.nome', read_only=True, default=None)

    class Meta:
        model = OrcamentoFinal
        fields = ['id', 'ordem_id', 'ordem_estado', 'ordem_estado_display', 'titulo', 'codigo',
                  'tipo_ambiente', 'tipo_ambiente_display', 'cidade', 'cliente_nome', 'designer_nome',
                  'marceneiro_nome', 'qtde_materiais', 'custo_materiais', 'horas_marceneiro',
                  'valor_hora', 'custo_mao_obra', 'comissao_designer', 'preco_total',
                  'mao_obra_confirmada', 'atualizado_em']


class OrcamentoFinalDetalheSerializer(OrcamentoFinalSerializer):
    materiais = serializers.SerializerMethodField()
    materiais_por_tipo = serializers.SerializerMethodField()
    pagamentos = serializers.SerializerMethodField()

    class Meta(OrcamentoFinalSerializer.Meta):
        fields = OrcamentoFinalSerializer.Meta.fields + ['materiais', 'materiais_por_tipo', 'pagamentos']

    def _materiais(self, obj):
        return list(obj.ordem.proposta_tecnica.materiais.all())

    def get_materiais(self, obj):
        return MaterialSerializer(self._materiais(obj), many=True).data

    def get_materiais_por_tipo(self, obj):
        """Subtotais por tipo de material (quantidade e custo)."""
        grupos = {}
        for m in self._materiais(obj):
            g = grupos.setdefault(m.tipo_material, {
                'tipo_material': m.tipo_material, 'rotulo': m.get_tipo_material_display(),
                'itens': 0, 'quantidade': 0.0, 'custo': 0.0})
            g['itens'] += 1
            g['quantidade'] += float(m.quantidade)
            g['custo'] += float(m.custo_total)
        return [{**g, 'quantidade': round(g['quantidade'], 2), 'custo': round(g['custo'], 2)}
                for g in grupos.values()]

    def get_pagamentos(self, obj):
        user = _usuario_logado(self)
        ordem = obj.ordem
        if not user or not (user.is_staff or ordem.necessidade.cliente_id == user.pk):
            return []
        qs = Pagamento.objects.filter(
            Q(proposta_tecnica=ordem.proposta_tecnica) | Q(proposta_marcenaria__ordem=ordem))
        return PagamentoSerializer(qs.order_by('data_transacao', 'id'), many=True).data


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id', 'mensagem', 'link', 'lida', 'criada_em']

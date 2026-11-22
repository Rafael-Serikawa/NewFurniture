from rest_framework import serializers

from .models import (Marceneiro, Material, Necessidade, Notificacao, OrdemServico, Pagamento,
                     PropostaTecnica, Usuario)


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


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id', 'mensagem', 'link', 'lida', 'criada_em']

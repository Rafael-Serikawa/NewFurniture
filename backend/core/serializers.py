from rest_framework import serializers

from .models import Marceneiro, Necessidade, OrdemServico, PropostaTecnica, Usuario


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
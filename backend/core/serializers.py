from rest_framework import serializers

from .models import Marceneiro, Notificacao, Usuario


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


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id', 'mensagem', 'link', 'lida', 'criada_em']

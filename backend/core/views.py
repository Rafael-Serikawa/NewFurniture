"""API REST do NewFurniture (Django REST Framework)."""

from django.contrib.auth import authenticate
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (action, api_view, authentication_classes,
                                       permission_classes)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Cliente, Designer, Marceneiro, Notificacao, Usuario
from .serializers import (LoginSerializer, NotificacaoSerializer, RegistroSerializer,
                          UsuarioSerializer)

T = Usuario.Tipo


# ---------------------------------------------------------------------------
# Autenticação e cadastro
# ---------------------------------------------------------------------------
def _resposta_login(user, status_code=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'usuario': UsuarioSerializer(user).data}, status=status_code)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def registro(request):
    """Cadastro de usuário: cria a especialização correta (Cliente/Designer/Marceneiro)."""
    ser = RegistroSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    dados = ser.validated_data
    classe = {'CLIENTE': Cliente, 'DESIGNER': Designer, 'MARCENEIRO': Marceneiro}[str(dados['tipo'])]
    user = classe(username=dados['email'], email=dados['email'], nome=dados['nome'].strip(),
                  tipo=dados['tipo'], cidade=dados.get('cidade', '').strip())
    user.set_password(dados['senha'])
    user.save()
    return _resposta_login(user, status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    ser = LoginSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    email = ser.validated_data['email'].strip().lower()
    user = authenticate(request, username=email, password=ser.validated_data['senha'])
    if user is None:
        return Response({'detail': 'E-mail ou senha incorretos.'}, status=status.HTTP_400_BAD_REQUEST)
    if not user.tipo:
        return Response({'detail': 'Conta administrativa: acesse /admin/ no backend.'},
                        status=status.HTTP_400_BAD_REQUEST)
    return _resposta_login(user)


@api_view(['POST'])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def eu(request):
    return Response(UsuarioSerializer(request.user).data)


def _papel(request):
    user = request.user
    if user.is_staff and not user.tipo:
        return 'ADMIN'
    return user.tipo


# ---------------------------------------------------------------------------
# Notificações
# ---------------------------------------------------------------------------
class NotificacaoViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificacaoSerializer

    def get_queryset(self):
        return Notificacao.objects.filter(usuario_id=self.request.user.pk)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return Response({
            'nao_lidas': qs.filter(lida=False).count(),
            'itens': NotificacaoSerializer(qs[:30], many=True).data,
        })

    @action(detail=True, methods=['post'])
    def lida(self, request, pk=None):
        self.get_queryset().filter(pk=pk).update(lida=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='marcar-todas')
    def marcar_todas(self, request):
        self.get_queryset().filter(lida=False).update(lida=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([AllowAny])
def status_api(request):
    return Response({'sistema': 'NewFurniture', 'status': 'ok'})

"""API REST do NewFurniture (Django REST Framework)."""

from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import Cliente, Designer, Marceneiro, Necessidade, Usuario
from .permissions import EhCliente
from .serializers import (LoginSerializer, NecessidadeSerializer, RegistroSerializer,
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
# Necessidades (NEC001)
# ---------------------------------------------------------------------------
class NecessidadeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    list:     cliente -> suas necessidades; designer -> mural (abertas + as que propôs)
    create:   cliente cadastra uma nova necessidade (multipart, com fotos)
    retrieve: detalhe com as propostas recebidas
    """

    def get_serializer_class(self):
        return NecessidadeSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), EhCliente()]
        return [IsAuthenticated()]

    def get_queryset(self):
        papel = _papel(self.request)
        qs = Necessidade.objects.select_related('cliente')
        if papel == T.CLIENTE:
            qs = qs.filter(cliente_id=self.request.user.pk)
        elif papel == T.DESIGNER:
            qs = qs.filter(Q(estado=Necessidade.Estado.ABERTA) |
                           Q(propostas__designer_id=self.request.user.pk)).distinct()
        elif papel != 'ADMIN':
            qs = qs.none()

        params = self.request.query_params
        if params.get('estado'):
            qs = qs.filter(estado=params['estado'].upper())
        if params.get('tipo_ambiente'):
            qs = qs.filter(tipo_ambiente=params['tipo_ambiente'].upper())
        if params.get('cidade'):
            qs = qs.filter(cidade__icontains=params['cidade'])
        if params.get('busca'):
            qs = qs.filter(Q(titulo__icontains=params['busca']) | Q(codigo__icontains=params['busca']))
        return qs

    def perform_create(self, serializer):
        necessidade = serializer.save(cliente_id=self.request.user.pk)
        # NEC001 passo 8: a necessidade fica visível para a rede de designers
        services.notificar(list(Designer.objects.all()),
                           f'Nova necessidade publicada: "{necessidade.titulo}" ({necessidade.cidade}).',
                           f'/projetos/{necessidade.pk}')


@api_view(['GET'])
@permission_classes([AllowAny])
def status_api(request):
    return Response({'sistema': 'NewFurniture', 'status': 'ok'})

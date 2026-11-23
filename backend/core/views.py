"""API REST do NewFurniture (Django REST Framework)."""
import json

from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (action, api_view, authentication_classes,
                                       permission_classes)
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import analitico, services
from .models import (Cliente, Designer, Marceneiro, Necessidade, Notificacao, OrcamentoFinal,
                     OrdemServico, Pagamento, PropostaTecnica, Usuario)
from .permissions import EhCliente, EhDesigner, EhMarceneiro
from .serializers import (DadosPagamentoSerializer, LoginSerializer, MaterialSerializer,
                          NecessidadeDetalheSerializer, NecessidadeSerializer,
                          NotificacaoSerializer, OrcamentoFinalDetalheSerializer,
                          OrcamentoFinalSerializer, OrdemServicoDetalheSerializer,
                          OrdemServicoSerializer, PagamentoSerializer, PropostaEntregaSerializer,
                          PropostaMarcenariaSerializer, PropostaTecnicaSerializer,
                          RegistroSerializer, UsuarioSerializer)

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
        return NecessidadeDetalheSerializer if self.action == 'retrieve' else NecessidadeSerializer

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


# ---------------------------------------------------------------------------
# Propostas técnicas (DES001 / APR001)
# ---------------------------------------------------------------------------
class PropostaTecnicaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                             mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = PropostaTecnicaSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), EhDesigner()]
        if self.action == 'aprovar':
            return [IsAuthenticated(), EhCliente()]
        return [IsAuthenticated()]

    def get_queryset(self):
        papel = _papel(self.request)
        qs = PropostaTecnica.objects.select_related('designer', 'necessidade') \
            .prefetch_related('materiais')
        if papel == T.DESIGNER:
            qs = qs.filter(designer_id=self.request.user.pk)
        elif papel == T.CLIENTE:
            qs = qs.filter(necessidade__cliente_id=self.request.user.pk)
        elif papel != 'ADMIN':
            qs = qs.none()
        if self.request.query_params.get('estado'):
            qs = qs.filter(estado=self.request.query_params['estado'].upper())
        return qs

    def create(self, request, *args, **kwargs):
        """Recebe multipart: desenho_tecnico (arquivo), dados da proposta e
        'materiais' como uma lista JSON [{tipo_material, descricao, quantidade,
        unidade, custo_unitario}, ...]."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bruto = request.data.get('materiais', '[]')
        try:
            materiais = json.loads(bruto) if isinstance(bruto, str) else bruto
        except ValueError:
            raise ValidationError({'materiais': ['Lista de materiais em formato inválido.']})
        if not isinstance(materiais, list) or not materiais:
            raise ValidationError({'materiais': ['Informe ao menos um material.']})
        materiais_ser = MaterialSerializer(data=materiais, many=True)
        materiais_ser.is_valid(raise_exception=True)

        necessidade = serializer.validated_data['necessidade']
        services.validar_nova_proposta_tecnica(necessidade, request.user)
        with transaction.atomic():
            proposta = serializer.save(designer_id=request.user.pk)
            materiais_ser.save(proposta=proposta)
        services.pos_submeter_proposta_tecnica(proposta)
        saida = self.get_serializer(PropostaTecnica.objects.get(pk=proposta.pk))
        return Response(saida.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        """APR001: aprova a proposta e processa o pagamento (checkout)."""
        proposta = self.get_object()
        dados = DadosPagamentoSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        pagamento, ordem = services.aprovar_proposta_tecnica(proposta, request.user, dados.validated_data)
        if ordem is None:
            return Response({
                'detail': 'Pagamento recusado pela operadora. Tente outro cartão.',
                'pagamento': PagamentoSerializer(pagamento).data,
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        return Response({'pagamento': PagamentoSerializer(pagamento).data, 'ordem_id': ordem.pk},
                        status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Ordens de serviço (MAR001, MAR002, ENT001, ENT002)
# ---------------------------------------------------------------------------
class OrdemServicoViewSet(viewsets.ReadOnlyModelViewSet):
    ACOES_CLIENTE = {'escolher_marceneiro', 'avaliar_entrega', 'confirmar_recebimento', 'redirecionar'}
    ACOES_MARCENEIRO = {'propor_execucao', 'iniciar_usinagem', 'recusar', 'finalizar', 'propor_entrega'}

    def get_serializer_class(self):
        return OrdemServicoSerializer if self.action == 'list' else OrdemServicoDetalheSerializer

    def get_permissions(self):
        if self.action in self.ACOES_CLIENTE:
            return [IsAuthenticated(), EhCliente()]
        if self.action in self.ACOES_MARCENEIRO:
            return [IsAuthenticated(), EhMarceneiro()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        papel = _papel(self.request)
        qs = OrdemServico.objects.select_related(
            'marceneiro', 'proposta_tecnica__designer', 'proposta_tecnica__necessidade__cliente')
        if papel == T.CLIENTE:
            qs = qs.filter(proposta_tecnica__necessidade__cliente_id=user.pk)
        elif papel == T.DESIGNER:
            qs = qs.filter(proposta_tecnica__designer_id=user.pk)
        elif papel == T.MARCENEIRO:
            qs = qs.filter(
                Q(marceneiro_id=user.pk) |
                Q(estado=OrdemServico.Estado.PENDENTE, marceneiro__isnull=True) |
                Q(propostas_marcenaria__marceneiro_id=user.pk)
            ).distinct()
        elif papel != 'ADMIN':
            qs = qs.none()

        escopo = self.request.query_params.get('escopo')
        if escopo == 'disponiveis':
            qs = qs.filter(estado=OrdemServico.Estado.PENDENTE, marceneiro__isnull=True)
        elif escopo == 'meus':
            qs = qs.filter(marceneiro_id=user.pk).exclude(estado=OrdemServico.Estado.ENTREGUE)
        elif escopo == 'ativos':
            qs = qs.exclude(estado=OrdemServico.Estado.ENTREGUE)
        elif escopo == 'historico':
            qs = qs.filter(estado=OrdemServico.Estado.ENTREGUE)
            if papel == T.MARCENEIRO:
                qs = qs.filter(marceneiro_id=user.pk)
        return qs

    def _detalhe(self, ordem, status_code=status.HTTP_200_OK):
        ordem = OrdemServico.objects.get(pk=ordem.pk)  # recarrega o estado atualizado
        return Response(OrdemServicoDetalheSerializer(ordem, context=self.get_serializer_context()).data,
                        status=status_code)

    # --- concorrência entre marceneiros ---
    @action(detail=True, methods=['post'], url_path='propor-execucao')
    def propor_execucao(self, request, pk=None):
        ordem = self.get_object()
        ser = PropostaMarcenariaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.propor_execucao(ordem, request.user, ser.validated_data)
        return self._detalhe(ordem, status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='escolher-marceneiro')
    def escolher_marceneiro(self, request, pk=None):
        ordem = self.get_object()
        dados = DadosPagamentoSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        try:
            proposta_id = int(request.data.get('proposta_marcenaria'))
        except (TypeError, ValueError):
            raise ValidationError({'proposta_marcenaria': ['Escolha uma proposta.']})
        pagamento = services.escolher_marceneiro(ordem, request.user, proposta_id, dados.validated_data)
        if pagamento.status != Pagamento.Status.APROVADO:
            return Response({
                'detail': 'Pagamento recusado pela operadora. Tente outro cartão.',
                'pagamento': PagamentoSerializer(pagamento).data,
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        return self._detalhe(ordem)

    # --- MAR001 ---
    @action(detail=True, methods=['post'], url_path='iniciar-usinagem')
    def iniciar_usinagem(self, request, pk=None):
        ordem = services.iniciar_usinagem(self.get_object(), request.user)
        return self._detalhe(ordem)

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        ordem = services.recusar_ordem(self.get_object(), request.user, request.data.get('motivo', ''))
        return self._detalhe(ordem)

    @action(detail=True, methods=['post'])
    def redirecionar(self, request, pk=None):
        ordem = services.redirecionar_ordem(self.get_object(), request.user)
        return self._detalhe(ordem)

    # --- MAR002 ---
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        ordem = services.finalizar_fabricacao(self.get_object(), request.user)
        return self._detalhe(ordem)

    # --- ENT001 ---
    @action(detail=True, methods=['post'], url_path='propor-entrega')
    def propor_entrega(self, request, pk=None):
        ordem = self.get_object()
        ser = PropostaEntregaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.propor_entrega(ordem, request.user, ser.validated_data)
        return self._detalhe(ordem, status.HTTP_201_CREATED)

    # --- ENT002 ---
    @action(detail=True, methods=['post'], url_path='avaliar-entrega')
    def avaliar_entrega(self, request, pk=None):
        ordem = self.get_object()
        services.avaliar_entrega(ordem, request.user, request.data.get('acao'),
                                 request.data.get('justificativa', ''))
        return self._detalhe(ordem)

    @action(detail=True, methods=['post'], url_path='confirmar-recebimento')
    def confirmar_recebimento(self, request, pk=None):
        ordem = services.confirmar_recebimento(self.get_object(), request.user)
        return self._detalhe(ordem)


# ---------------------------------------------------------------------------
# Orçamento final (entidade multidimensional) e totalizações
# ---------------------------------------------------------------------------
class OrcamentoFinalViewSet(viewsets.ReadOnlyModelViewSet):

    def get_serializer_class(self):
        return OrcamentoFinalDetalheSerializer if self.action == 'retrieve' else OrcamentoFinalSerializer

    def get_queryset(self):
        user = self.request.user
        papel = _papel(self.request)
        qs = OrcamentoFinal.objects.select_related(
            'ordem__marceneiro', 'ordem__proposta_tecnica__designer',
            'ordem__proposta_tecnica__necessidade__cliente',
        ).prefetch_related('ordem__proposta_tecnica__materiais').order_by('-ordem__criado_em', '-id')
        if papel == T.CLIENTE:
            qs = qs.filter(ordem__proposta_tecnica__necessidade__cliente_id=user.pk)
        elif papel == T.DESIGNER:
            qs = qs.filter(ordem__proposta_tecnica__designer_id=user.pk)
        elif papel == T.MARCENEIRO:
            qs = qs.filter(ordem__marceneiro_id=user.pk)
        elif papel != 'ADMIN':
            qs = qs.none()
        if self.request.query_params.get('incluir_cancelados') != '1':
            qs = qs.exclude(ordem__estado=OrdemServico.Estado.CANCELADA)
        return qs

    @action(detail=False)
    def totalizacao(self, request):
        """GET /api/orcamentos/totalizacao/?dimensao=tipo_ambiente"""
        dimensao = request.query_params.get('dimensao', 'tipo_ambiente')
        try:
            dados = analitico.totalizar(self.get_queryset(), dimensao)
        except ValueError as erro:
            raise ValidationError({'detail': str(erro)})
        return Response(dados)

    @action(detail=False)
    def cubo(self, request):
        """GET /api/orcamentos/cubo/?linhas=tipo_ambiente&colunas=estado&medida=preco_total"""
        p = request.query_params
        try:
            dados = analitico.cubo(self.get_queryset(), p.get('linhas', 'tipo_ambiente'),
                                   p.get('colunas', 'estado'), p.get('medida', 'preco_total'))
        except ValueError as erro:
            raise ValidationError({'detail': str(erro)})
        return Response(dados)

    @action(detail=False)
    def dimensoes(self, request):
        """Lista as dimensões e medidas disponíveis para montar o cubo."""
        return Response({
            'dimensoes': [{'chave': k, 'rotulo': v} for k, v in analitico.DIMENSOES.items()],
            'medidas': [{'chave': k, 'rotulo': v} for k, v in analitico.MEDIDAS.items()],
            'medidas_material': analitico.MEDIDAS_MATERIAL,
        })


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

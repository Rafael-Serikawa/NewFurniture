"""
Testes automatizados da API — percorrem o fluxo completo dos casos de uso.

    python manage.py test core
"""
import json
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Necessidade, OrdemServico, Pagamento, PropostaTecnica

MEDIA_TESTE = tempfile.mkdtemp()

# PNG 1x1 válido
PNG = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f'
       b'\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00'
       b'IEND\xaeB`\x82')
CARTAO_OK = {'nome_titular': 'ANA', 'numero_cartao': '4111111111111111', 'validade': '12/29', 'cvv': '123'}
CARTAO_RECUSADO = {**CARTAO_OK, 'numero_cartao': '4111111111110000'}


def imagem(nome='foto.png'):
    return SimpleUploadedFile(nome, PNG, content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA_TESTE)
class FluxoCompletoTest(APITestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TESTE, ignore_errors=True)
        super().tearDownClass()

    def registrar(self, nome, email, tipo):
        r = self.client.post('/api/auth/registro/', {'nome': nome, 'email': email, 'senha': 'senha123',
                                                     'tipo': tipo, 'cidade': 'São Paulo'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        return r.data['token']

    def como(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def setUp(self):
        self.t_cliente = self.registrar('Ana', 'ana@teste.com', 'CLIENTE')
        self.t_designer = self.registrar('Carla', 'carla@teste.com', 'DESIGNER')
        self.t_designer2 = self.registrar('Diego', 'diego@teste.com', 'DESIGNER')
        self.t_marceneiro = self.registrar('Edu', 'edu@teste.com', 'MARCENEIRO')
        self.t_marceneiro2 = self.registrar('Fabio', 'fabio@teste.com', 'MARCENEIRO')

    # ------------------------------------------------------------------ passos
    def criar_necessidade(self):
        self.como(self.t_cliente)
        r = self.client.post('/api/necessidades/', {
            'titulo': 'Armário de cozinha', 'cidade': 'São Paulo', 'tipo_ambiente': 'COZINHA',
            'largura': '180', 'altura': '70', 'profundidade': '35', 'custo_esperado': '3000',
            'foto_ambiente': imagem(), 'observacoes': 'Portas brancas',
        }, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(r.data['codigo']), 8)
        self.assertEqual(r.data['estado'], 'ABERTA')
        return r.data['id']

    def enviar_proposta(self, token, necessidade_id, comissao='500'):
        self.como(token)
        materiais = [
            {'tipo_material': 'MDF', 'descricao': 'MDF 18mm', 'quantidade': '4', 'unidade': 'm2',
             'custo_unitario': '100'},
            {'tipo_material': 'FERRAGEM', 'descricao': 'Dobradiça', 'quantidade': '6', 'unidade': 'un',
             'custo_unitario': '10'},
        ]
        r = self.client.post('/api/propostas-tecnicas/', {
            'necessidade': necessidade_id, 'desenho_tecnico': imagem('desenho.png'),
            'comissao_designer': comissao, 'horas_estimadas': '10', 'materiais': json.dumps(materiais),
        }, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['custo_materiais'], 460.0)
        return r.data['id']

    # ------------------------------------------------------------------ testes
    def test_login_e_perfil(self):
        r = self.client.post('/api/auth/login/', {'email': 'ANA@teste.com', 'senha': 'senha123'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.como(r.data['token'])
        self.assertEqual(self.client.get('/api/auth/eu/').data['tipo'], 'CLIENTE')
        r = self.client.post('/api/auth/login/', {'email': 'ana@teste.com', 'senha': 'errada'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_validacao_necessidade(self):
        self.como(self.t_cliente)
        r = self.client.post('/api/necessidades/', {
            'titulo': 'X', 'cidade': 'SP', 'tipo_ambiente': 'COZINHA', 'largura': '-5', 'altura': '10',
            'profundidade': '10', 'custo_esperado': '10',
            'foto_ambiente': SimpleUploadedFile('a.txt', b'abc', content_type='text/plain'),
        }, format='multipart')
        self.assertEqual(r.status_code, 400)
        self.assertIn('largura', r.data)
        self.assertIn('foto_ambiente', r.data)

    def test_permissoes_por_perfil(self):
        nid = self.criar_necessidade()
        # designer não pode cadastrar necessidade
        self.como(self.t_designer)
        r = self.client.post('/api/necessidades/', {'titulo': 'x'}, format='multipart')
        self.assertEqual(r.status_code, 403)
        # designer vê o mural de abertas
        r = self.client.get('/api/necessidades/?estado=ABERTA')
        self.assertEqual([n['id'] for n in r.data], [nid])
        # marceneiro não vê necessidades
        self.como(self.t_marceneiro)
        self.assertEqual(self.client.get('/api/necessidades/').data, [])

    def test_fluxo_completo(self):
        nid = self.criar_necessidade()
        p1 = self.enviar_proposta(self.t_designer, nid)
        p2 = self.enviar_proposta(self.t_designer2, nid, comissao='300')

        # designer não pode enviar duas propostas para a mesma necessidade
        self.como(self.t_designer)
        materiais = json.dumps([{'tipo_material': 'MDF', 'descricao': 'x', 'quantidade': '1',
                                 'unidade': 'm2', 'custo_unitario': '1'}])
        r = self.client.post('/api/propostas-tecnicas/', {
            'necessidade': nid, 'desenho_tecnico': imagem(), 'comissao_designer': '1',
            'materiais': materiais}, format='multipart')
        self.assertEqual(r.status_code, 400)

        # cliente vê as duas propostas
        self.como(self.t_cliente)
        r = self.client.get(f'/api/necessidades/{nid}/')
        self.assertEqual(len(r.data['propostas']), 2)

        # APR001 - pagamento recusado (fluxo alternativo)
        r = self.client.post(f'/api/propostas-tecnicas/{p1}/aprovar/', CARTAO_RECUSADO, format='json')
        self.assertEqual(r.status_code, 402)
        self.assertEqual(Pagamento.objects.get().status, 'RECUSADO')
        self.assertEqual(Necessidade.objects.get(pk=nid).estado, 'ABERTA')

        # APR001 - pagamento aprovado
        r = self.client.post(f'/api/propostas-tecnicas/{p1}/aprovar/', CARTAO_OK, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        oid = r.data['ordem_id']
        self.assertEqual(Necessidade.objects.get(pk=nid).estado, 'RESOLVIDA')
        self.assertEqual(PropostaTecnica.objects.get(pk=p1).estado, 'APROVADA')
        self.assertEqual(PropostaTecnica.objects.get(pk=p2).estado, 'ARQUIVADA')
        self.assertEqual(OrdemServico.objects.get(pk=oid).estado, 'PENDENTE')

        # orçamento estimado: 460 materiais + 500 comissão + 10h * 60
        r = self.client.get(f'/api/ordens/{oid}/')
        self.assertEqual(r.data['orcamento']['preco_total'], 1560.0)
        self.assertFalse(r.data['orcamento']['mao_obra_confirmada'])

        # marceneiros enviam propostas de execução
        self.como(self.t_marceneiro)
        self.assertEqual(len(self.client.get('/api/ordens/?escopo=disponiveis').data), 1)
        r = self.client.post(f'/api/ordens/{oid}/propor-execucao/', {
            'horas_trabalho': '12', 'valor_hora': '70', 'prazo_estimado_dias': 10}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        pm1 = r.data['propostas_marcenaria'][0]['id']
        self.como(self.t_marceneiro2)
        r = self.client.post(f'/api/ordens/{oid}/propor-execucao/', {
            'horas_trabalho': '15', 'valor_hora': '50', 'prazo_estimado_dias': 8}, format='json')
        self.assertEqual(r.status_code, 201, r.data)

        # cliente escolhe o marceneiro 1 e paga a execução
        self.como(self.t_cliente)
        r = self.client.get(f'/api/ordens/{oid}/')
        self.assertEqual(len(r.data['propostas_marcenaria']), 2)
        r = self.client.post(f'/api/ordens/{oid}/escolher-marceneiro/',
                             {**CARTAO_OK, 'proposta_marcenaria': pm1}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['marceneiro_nome'], 'Edu')
        self.assertEqual(r.data['orcamento']['preco_total'], 460 + 500 + 12 * 70)
        self.assertTrue(r.data['orcamento']['mao_obra_confirmada'])

        # MAR001 - outro marceneiro não pode iniciar
        self.como(self.t_marceneiro2)
        r = self.client.post(f'/api/ordens/{oid}/iniciar-usinagem/')
        self.assertEqual(r.status_code, 404)

        # MAR001 / MAR002
        self.como(self.t_marceneiro)
        r = self.client.post(f'/api/ordens/{oid}/iniciar-usinagem/')
        self.assertEqual(r.data['estado'], 'EM_USINAGEM')
        r = self.client.post(f'/api/ordens/{oid}/finalizar/')
        self.assertEqual(r.data['estado'], 'FINALIZADA')

        # ENT001 / ENT002 com contraproposta
        entrega = {'modalidade': 'DELIVERY', 'local': 'Rua A, 1', 'prazo': '2026-12-10',
                   'horarios_disponiveis': 'Seg 14h-18h'}
        r = self.client.post(f'/api/ordens/{oid}/propor-entrega/', entrega, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.como(self.t_cliente)
        r = self.client.post(f'/api/ordens/{oid}/avaliar-entrega/', {'acao': 'alterar'}, format='json')
        self.assertEqual(r.status_code, 400)  # justificativa obrigatória
        r = self.client.post(f'/api/ordens/{oid}/avaliar-entrega/',
                             {'acao': 'alterar', 'justificativa': 'Prefiro sábado'}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.como(self.t_marceneiro)
        r = self.client.post(f'/api/ordens/{oid}/propor-entrega/',
                             {**entrega, 'horarios_disponiveis': 'Sáb 9h-12h'}, format='json')
        self.assertEqual(len(r.data['propostas_entrega']), 2)
        self.como(self.t_cliente)
        r = self.client.post(f'/api/ordens/{oid}/avaliar-entrega/', {'acao': 'aprovar'}, format='json')
        self.assertEqual(r.data['estado'], 'ENTREGA_ACORDADA')
        r = self.client.post(f'/api/ordens/{oid}/confirmar-recebimento/')
        self.assertEqual(r.data['estado'], 'ENTREGUE')

        # histórico e totalizações
        self.assertEqual(len(self.client.get('/api/ordens/?escopo=historico').data), 1)
        r = self.client.get('/api/orcamentos/totalizacao/?dimensao=tipo_material')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['total']['custo_materiais'], 460.0)
        r = self.client.get('/api/orcamentos/cubo/?linhas=tipo_ambiente&colunas=estado&medida=preco_total')
        self.assertEqual(r.data['total_geral'], 1800.0)
        orc = self.client.get('/api/orcamentos/').data[0]['id']
        r = self.client.get(f'/api/orcamentos/{orc}/')
        self.assertEqual(len(r.data['materiais_por_tipo']), 2)
        self.assertEqual(len(r.data['pagamentos']), 3)  # recusado + projeto + execução

        # notificações geradas ao longo do fluxo
        self.como(self.t_designer)
        self.assertGreater(self.client.get('/api/notificacoes/').data['nao_lidas'], 0)

    def test_recusa_e_redirecionamento(self):
        nid = self.criar_necessidade()
        p1 = self.enviar_proposta(self.t_designer, nid)
        self.como(self.t_cliente)
        oid = self.client.post(f'/api/propostas-tecnicas/{p1}/aprovar/', CARTAO_OK, format='json').data['ordem_id']
        self.como(self.t_marceneiro)
        pm = self.client.post(f'/api/ordens/{oid}/propor-execucao/', {
            'horas_trabalho': '10', 'valor_hora': '60', 'prazo_estimado_dias': 5},
            format='json').data['propostas_marcenaria'][0]['id']
        self.como(self.t_cliente)
        self.client.post(f'/api/ordens/{oid}/escolher-marceneiro/', {**CARTAO_OK, 'proposta_marcenaria': pm},
                         format='json')
        self.como(self.t_marceneiro)
        r = self.client.post(f'/api/ordens/{oid}/recusar/', {'motivo': ''}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.client.post(f'/api/ordens/{oid}/recusar/', {'motivo': 'Sem CNC disponível'}, format='json')
        self.assertEqual(r.data['estado'], 'CANCELADA')
        self.assertEqual(Pagamento.objects.get(tipo_servico='EXECUCAO').status, 'REEMBOLSADO')
        self.como(self.t_cliente)
        r = self.client.post(f'/api/ordens/{oid}/redirecionar/')
        self.assertEqual(r.data['estado'], 'PENDENTE')
        self.assertIsNone(r.data['marceneiro_id'])
        # o projeto técnico continua o mesmo
        self.assertEqual(r.data['proposta_tecnica']['id'], p1)

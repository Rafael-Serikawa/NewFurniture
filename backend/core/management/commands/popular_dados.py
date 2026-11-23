"""
python manage.py popular_dados [--limpar]

Cria usuários de demonstração e projetos em TODOS os estados do fluxo, para que
cada caso de uso possa ser demonstrado na apresentação.
Senha de todas as contas: senha123
"""
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core import services
from core.models import (Cliente, Designer, Marceneiro, Material, Necessidade, Notificacao,
                         OrdemServico, PropostaTecnica, Usuario)

SEED_DIR = Path(__file__).resolve().parents[2] / 'seed'
SENHA = 'senha123'
CARTAO = {'nome_titular': 'CLIENTE DEMO', 'numero_cartao': '4111 1111 1111 1111',
          'validade': '12/29', 'cvv': '123'}
TIPO = {Cliente: Usuario.Tipo.CLIENTE, Designer: Usuario.Tipo.DESIGNER,
        Marceneiro: Usuario.Tipo.MARCENEIRO}
A = Necessidade.Ambiente
M = Material.Tipo


def arquivo(nome):
    return ContentFile((SEED_DIR / nome).read_bytes(), name=nome)


def D(valor):
    return Decimal(str(valor))


class Command(BaseCommand):
    help = 'Popula o banco com usuários e projetos de demonstração (senha: senha123).'

    def add_arguments(self, parser):
        parser.add_argument('--limpar', action='store_true',
                            help='Apaga todos os dados (exceto superusuários) antes de popular.')

    def handle(self, *args, **opts):
        if opts['limpar']:
            Usuario.objects.filter(is_superuser=False).delete()
            self.stdout.write('Dados anteriores apagados.')
        if Usuario.objects.filter(email='ana@cliente.com').exists():
            self.stdout.write(self.style.WARNING(
                'Os dados de demonstração já existem. Use --limpar para recriá-los.'))
            return
        with transaction.atomic():
            self.agora = timezone.now()
            self._popular()
        self.stdout.write(self.style.SUCCESS('Dados de demonstração criados!'))
        self.stdout.write('Contas (senha: senha123):')
        for email in ['ana@cliente.com', 'bruno@cliente.com', 'carla@designer.com',
                      'diego@designer.com', 'eduardo@marceneiro.com', 'fabio@marceneiro.com']:
            self.stdout.write(f'  - {email}')

    # ------------------------------------------------------------------ helpers
    def usuario(self, classe, nome, email, cidade, **extra):
        u = classe(username=email, email=email, nome=nome, tipo=TIPO[classe], cidade=cidade, **extra)
        u.set_password(SENHA)
        u.save()
        return u

    def necessidade(self, cliente, titulo, ambiente, dims, foto, custo, obs='', esboco=None, dias=0):
        n = Necessidade(cliente=cliente, titulo=titulo, cidade=cliente.cidade, tipo_ambiente=ambiente,
                        largura=D(dims[0]), altura=D(dims[1]), profundidade=D(dims[2]),
                        foto_ambiente=arquivo(foto), observacoes=obs, custo_esperado=custo)
        if esboco:
            n.esboco_movel = arquivo(esboco)
        n.save()
        Necessidade.objects.filter(pk=n.pk).update(criado_em=self.agora - timedelta(days=dias))
        return n

    def proposta(self, necessidade, designer, desenho, comissao, horas, materiais, descricao='', dias=0):
        p = PropostaTecnica.objects.create(
            necessidade=necessidade, designer=designer, desenho_tecnico=arquivo(desenho),
            descricao=descricao, comissao_designer=D(comissao), horas_estimadas=D(horas))
        for tipo, desc, qtd, unidade, custo in materiais:
            Material.objects.create(proposta=p, tipo_material=tipo, descricao=desc, quantidade=D(qtd),
                                    unidade=unidade, custo_unitario=D(custo))
        services.pos_submeter_proposta_tecnica(p)
        PropostaTecnica.objects.filter(pk=p.pk).update(criado_em=self.agora - timedelta(days=dias))
        return p

    def contratar(self, proposta, cliente, marceneiro, horas, prazo, dias, outros=()):
        """APR001 + proposta(s) de marcenaria + escolha do marceneiro."""
        _, ordem = services.aprovar_proposta_tecnica(proposta, cliente, CARTAO)
        escolhida = None
        for m, h in [(marceneiro, horas)] + list(outros):
            pm = services.propor_execucao(ordem, m, {
                'horas_trabalho': D(h), 'valor_hora': m.valor_hora, 'prazo_estimado_dias': prazo,
                'descricao': 'Corte CNC, fitagem de bordas, furação para montagem e embalagem do kit.'})
            escolhida = escolhida or pm
        services.escolher_marceneiro(ordem, cliente, escolhida.pk, CARTAO)
        OrdemServico.objects.filter(pk=ordem.pk).update(criado_em=self.agora - timedelta(days=dias))
        return ordem

    def entrega(self, ordem, marceneiro, modalidade, local, horarios, dias_prazo, instrucoes=''):
        return services.propor_entrega(ordem, marceneiro, {
            'modalidade': modalidade, 'local': local, 'horarios_disponiveis': horarios,
            'prazo': timezone.localdate() + timedelta(days=dias_prazo), 'instrucoes': instrucoes})

    # ----------------------------------------------------------------- dados
    def _popular(self):
        ana = self.usuario(Cliente, 'Ana Souza', 'ana@cliente.com', 'São Paulo')
        bruno = self.usuario(Cliente, 'Bruno Lima', 'bruno@cliente.com', 'Campinas')
        carla = self.usuario(Designer, 'Carla Mendes', 'carla@designer.com', 'São Paulo',
                             especialidade='Cozinhas e dormitórios')
        diego = self.usuario(Designer, 'Diego Ramos', 'diego@designer.com', 'Santo André',
                             especialidade='Salas e home office')
        eduardo = self.usuario(Marceneiro, 'Eduardo Alves', 'eduardo@marceneiro.com', 'São Paulo',
                               valor_hora=D(65))
        fabio = self.usuario(Marceneiro, 'Fábio Costa', 'fabio@marceneiro.com', 'Campinas',
                             valor_hora=D(55))

        # 1) ABERTA com duas propostas concorrentes -> demonstra APR001 (Ana)
        n1 = self.necessidade(
            ana, 'Armário suspenso para cozinha', A.COZINHA, (180, 70, 35), 'foto_cozinha.jpg', 3500,
            'Quero portas brancas e puxador cava. O armário fica acima da pia.',
            esboco='esboco_armario.png', dias=6)
        self.proposta(n1, carla, 'desenho_armario_a.png', 600, 16, [
            (M.MDF, 'Chapa MDF 18 mm branco TX', 4.2, 'm2', 95),
            (M.FERRAGEM, 'Dobradiça com amortecedor', 6, 'un', 12),
            (M.FERRAGEM, 'Fita de borda PVC branca', 14, 'm', 2.5),
        ], 'Três módulos com portas de abrir e prateleira regulável.', dias=4)
        self.proposta(n1, diego, 'desenho_armario_b.png', 450, 18, [
            (M.MDF, 'Chapa MDF 15 mm branco', 4.5, 'm2', 80),
            (M.FERRAGEM, 'Pistão para porta basculante', 4, 'un', 38),
            (M.FERRAGEM, 'Fita de borda PVC branca', 16, 'm', 2.5),
        ], 'Quatro portas basculantes, mais fácil de abrir acima da pia.', dias=2)

        # 2) ABERTA sem propostas -> demonstra DES001 (designers)
        n2 = self.necessidade(
            ana, 'Estante para home office', A.ESCRITORIO, (160, 200, 35), 'foto_escritorio.jpg', 2800,
            'Estante com nichos abertos e uma parte com portas para esconder papéis.', dias=1)

        # 3) ABERTA com uma proposta (Diego) -> Carla ainda pode propor
        n3 = self.necessidade(
            bruno, 'Rack baixo para sala', A.SALA, (200, 50, 45), 'foto_sala.jpg', 1800,
            'Precisa ter espaço para o videogame e passagem de cabos.', dias=3)
        self.proposta(n3, diego, 'desenho_rack.png', 350, 12, [
            (M.MDF, 'Chapa MDF 18 mm carvalho', 3.1, 'm2', 110),
            (M.FERRAGEM, 'Dobradiça com amortecedor', 4, 'un', 12),
        ], 'Duas portas e nicho central com furação para cabos.', dias=1)

        # 4) OS PENDENTE aguardando escolha do marceneiro (Eduardo já propôs)
        n4 = self.necessidade(ana, 'Guarda-roupa de casal', A.QUARTO, (210, 240, 60), 'foto_quarto.jpg',
                              6500, 'Três portas de correr não cabem; prefiro portas de abrir.', dias=12)
        p4 = self.proposta(n4, carla, 'desenho_guarda_roupa.png', 1200, 40, [
            (M.MDF, 'Chapa MDF 18 mm branco TX', 12.5, 'm2', 95),
            (M.COMPENSADO, 'Fundo em compensado 6 mm', 5, 'm2', 38),
            (M.ACO, 'Tubo cabideiro oblongo', 3, 'm', 22),
            (M.FERRAGEM, 'Dobradiça com amortecedor', 12, 'un', 12),
        ], dias=10)
        _, os4 = services.aprovar_proposta_tecnica(p4, ana, CARTAO)
        services.propor_execucao(os4, eduardo, {
            'horas_trabalho': D(42), 'valor_hora': eduardo.valor_hora, 'prazo_estimado_dias': 15,
            'descricao': 'Fabrico em 15 dias, com montagem facilitada por cavilhas.'})
        OrdemServico.objects.filter(pk=os4.pk).update(criado_em=self.agora - timedelta(days=8))

        # 5) OS PENDENTE com Fábio escolhido -> demonstra MAR001 (iniciar / recusar)
        n5 = self.necessidade(bruno, 'Sapateira para o quarto', A.QUARTO, (90, 120, 35),
                              'foto_quarto.jpg', 1200, dias=18)
        p5 = self.proposta(n5, diego, 'desenho_sapateira.png', 250, 10, [
            (M.MDF, 'Chapa MDF 15 mm cinza', 2.6, 'm2', 85),
            (M.FERRAGEM, 'Suporte de prateleira', 20, 'un', 1.5),
        ], dias=16)
        os5 = self.contratar(p5, bruno, fabio, 11, 7, dias=14)

        # 6) EM USINAGEM com Eduardo -> demonstra MAR002 (finalizar)
        n6 = self.necessidade(bruno, 'Painel de TV com rack', A.SALA, (220, 180, 40), 'foto_sala.jpg',
                              4200, 'TV de 65 polegadas.', dias=30)
        p6 = self.proposta(n6, diego, 'desenho_painel.png', 700, 28, [
            (M.MDF, 'Chapa MDF 18 mm freijó', 7.8, 'm2', 120),
            (M.FERRAGEM, 'Corrediça telescópica', 4, 'un', 28),
            (M.ACO, 'Suporte articulado para TV', 1, 'un', 180),
        ], dias=27)
        os6 = self.contratar(p6, bruno, eduardo, 30, 12, dias=25, outros=[(fabio, 34)])
        services.iniciar_usinagem(os6, eduardo)

        # 7) FINALIZADA sem proposta de entrega (Eduardo) -> demonstra ENT001
        n7 = self.necessidade(bruno, 'Cabeceira estofada com nichos', A.QUARTO, (160, 110, 12),
                              'foto_quarto.jpg', 1500, dias=40)
        p7 = self.proposta(n7, carla, 'desenho_cabeceira.png', 300, 9, [
            (M.MDF, 'Chapa MDF 15 mm', 1.8, 'm2', 80),
            (M.OUTRO, 'Espuma D33 + tecido linho', 2, 'm2', 70),
        ], dias=37)
        os7 = self.contratar(p7, bruno, eduardo, 10, 6, dias=35)
        services.iniciar_usinagem(os7, eduardo)
        services.finalizar_fabricacao(os7, eduardo)

        # 8) FINALIZADA com proposta de entrega aguardando o cliente -> demonstra ENT002
        n8 = self.necessidade(ana, 'Gabinete de banheiro', A.BANHEIRO, (80, 55, 45), 'foto_banheiro.jpg',
                              1600, 'Material resistente à umidade.', dias=45)
        p8 = self.proposta(n8, carla, 'desenho_gabinete.png', 280, 8, [
            (M.MDF, 'Chapa MDF ultra (resistente à umidade) 18 mm', 1.6, 'm2', 140),
            (M.FERRAGEM, 'Corrediça telescópica', 2, 'un', 28),
        ], dias=43)
        os8 = self.contratar(p8, ana, fabio, 9, 6, dias=40)
        services.iniciar_usinagem(os8, fabio)
        services.finalizar_fabricacao(os8, fabio)
        self.entrega(os8, fabio, 'DELIVERY', 'Rua Augusta, 1500 — São Paulo', 'Seg a sex, 14h às 18h', 4)
        services.avaliar_entrega(os8, ana, 'alterar',
                                 'Durante a semana não há ninguém em casa. Pode ser no sábado de manhã?')
        self.entrega(os8, fabio, 'DELIVERY', 'Rua Augusta, 1500 — São Paulo', 'Sábado, 9h às 12h', 6,
                     'Kit em 3 volumes; o maior tem 85 cm.')

        # 9) e 10) ENTREGUES -> histórico de projetos concluídos
        n9 = self.necessidade(ana, 'Banco de jardim com baú', A.AREA_EXTERNA, (150, 45, 50),
                              'foto_externa.jpg', 2200, 'Vai ficar exposto ao tempo.', dias=80)
        p9 = self.proposta(n9, diego, 'desenho_banco.png', 400, 14, [
            (M.MADEIRA_DE_LEI, 'Tábuas de cumaru 2 cm', 2.2, 'm2', 260),
            (M.ACO, 'Parafusos inox', 40, 'un', 0.9),
            (M.OUTRO, 'Verniz marítimo', 1, 'un', 95),
        ], dias=77)
        os9 = self.contratar(p9, ana, eduardo, 16, 10, dias=74)
        services.iniciar_usinagem(os9, eduardo)
        services.finalizar_fabricacao(os9, eduardo)
        self.entrega(os9, eduardo, 'RETIRADA', 'Marcenaria Alves — Rua do Bosque, 80, São Paulo',
                     'Sábado, 8h às 13h', -20)
        services.avaliar_entrega(os9, ana, 'aprovar')
        services.confirmar_recebimento(os9, ana)

        n10 = self.necessidade(bruno, 'Mesa de escritório com gaveteiro', A.ESCRITORIO, (140, 75, 60),
                               'foto_escritorio.jpg', 2000, dias=65)
        p10 = self.proposta(n10, carla, 'desenho_mesa.png', 380, 15, [
            (M.MDF, 'Chapa MDF 25 mm carvalho', 2.4, 'm2', 150),
            (M.ACO, 'Pés em aço carbono preto', 4, 'un', 45),
            (M.FERRAGEM, 'Corrediça telescópica', 6, 'un', 28),
        ], dias=63)
        os10 = self.contratar(p10, bruno, fabio, 14, 8, dias=60)
        services.iniciar_usinagem(os10, fabio)
        services.finalizar_fabricacao(os10, fabio)
        self.entrega(os10, fabio, 'DELIVERY', 'Av. Norte-Sul, 300 — Campinas', 'Seg a sex, 9h às 12h', -15)
        services.avaliar_entrega(os10, bruno, 'aprovar')
        services.confirmar_recebimento(os10, bruno)

        # Notificações: tudo como lido, exceto as pendências que valem demonstrar
        Notificacao.objects.update(lida=True)
        pendencias = [
            (ana, f'Nova proposta de Diego Ramos para "{n1.titulo}".', f'/pedidos/{n1.pk}'),
            (ana, f'Eduardo Alves enviou uma proposta de execução para "{n4.titulo}".', f'/ordens/{os4.pk}'),
            (ana, f'Proposta de entrega para "{n8.titulo}" aguardando sua avaliação.', f'/ordens/{os8.pk}'),
            (carla, f'Nova necessidade publicada: "{n2.titulo}" (São Paulo).', f'/projetos/{n2.pk}'),
            (diego, f'Nova necessidade publicada: "{n2.titulo}" (São Paulo).', f'/projetos/{n2.pk}'),
            (eduardo, f'"{n7.titulo}" está finalizada: proponha o método de entrega.', f'/ordens/{os7.pk}'),
            (fabio, f'Você foi escolhido para fabricar "{n5.titulo}". Inicie a usinagem!', f'/ordens/{os5.pk}'),
            (fabio, f'Nova ordem de serviço disponível: "{n4.titulo}".', f'/ordens/{os4.pk}'),
        ]
        for usuario, mensagem, link in pendencias:
            services.notificar([usuario], mensagem, link)
        _ = (n3, os6)  # usados apenas para criar os estados acima

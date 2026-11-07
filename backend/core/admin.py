from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (Cliente, Designer, Marceneiro, Material, Necessidade, Notificacao,
                     OrcamentoFinal, OrdemServico, Pagamento, PropostaEntrega, PropostaMarcenaria,
                     PropostaTecnica, Usuario)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'nome', 'email', 'tipo', 'cidade', 'is_staff')
    list_filter = ('tipo', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (('NewFurniture', {'fields': ('nome', 'tipo', 'cidade')}),)


@admin.register(Cliente, Designer)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'cidade')
    search_fields = ('nome', 'email')
    exclude = ('password', 'groups', 'user_permissions', 'last_login')


@admin.register(Marceneiro)
class MarceneiroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'cidade', 'valor_hora')
    search_fields = ('nome', 'email')
    exclude = ('password', 'groups', 'user_permissions', 'last_login')


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 0


class PropostaTecnicaInline(admin.TabularInline):
    model = PropostaTecnica
    extra = 0
    fields = ('designer', 'estado', 'comissao_designer', 'horas_estimadas')
    show_change_link = True


@admin.register(Necessidade)
class NecessidadeAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'titulo', 'cliente', 'tipo_ambiente', 'cidade', 'estado', 'criado_em')
    list_filter = ('estado', 'tipo_ambiente')
    search_fields = ('codigo', 'titulo', 'cidade')
    inlines = [PropostaTecnicaInline]


@admin.register(PropostaTecnica)
class PropostaTecnicaAdmin(admin.ModelAdmin):
    list_display = ('id', 'necessidade', 'designer', 'estado', 'comissao_designer', 'criado_em')
    list_filter = ('estado',)
    inlines = [MaterialInline]


class PropostaMarcenariaInline(admin.TabularInline):
    model = PropostaMarcenaria
    extra = 0


class PropostaEntregaInline(admin.StackedInline):
    model = PropostaEntrega
    extra = 0


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'proposta_tecnica', 'marceneiro', 'estado', 'criado_em')
    list_filter = ('estado',)
    inlines = [PropostaMarcenariaInline, PropostaEntregaInline]


@admin.register(OrcamentoFinal)
class OrcamentoFinalAdmin(admin.ModelAdmin):
    list_display = ('ordem', 'custo_materiais', 'custo_mao_obra', 'comissao_designer', 'preco_total',
                    'mao_obra_confirmada')
    actions = ['recalcular']

    @admin.action(description='Recalcular orçamentos selecionados')
    def recalcular(self, request, queryset):
        for orcamento in queryset:
            orcamento.recalcular()


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo_servico', 'valor', 'status', 'cartao_final', 'data_transacao')
    list_filter = ('status', 'tipo_servico')


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'mensagem', 'lida', 'criada_em')
    list_filter = ('lida',)

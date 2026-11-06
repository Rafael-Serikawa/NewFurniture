from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Cliente, Designer, Marceneiro, Usuario


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

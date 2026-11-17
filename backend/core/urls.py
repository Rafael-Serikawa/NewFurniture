from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('necessidades', views.NecessidadeViewSet, basename='necessidade')
router.register('propostas-tecnicas', views.PropostaTecnicaViewSet, basename='proposta-tecnica')
router.register('notificacoes', views.NotificacaoViewSet, basename='notificacao')

urlpatterns = [
    path('status/', views.status_api, name='status'),
    path('auth/registro/', views.registro, name='registro'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/eu/', views.eu, name='eu'),
    path('', include(router.urls)),
]

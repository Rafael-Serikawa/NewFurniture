from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

urlpatterns = [
    path('status/', views.status_api, name='status'),
    path('', include(router.urls)),
]

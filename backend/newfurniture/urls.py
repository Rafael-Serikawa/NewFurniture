from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve


def frontend_index(request):
    """Serve o build do React (frontend/dist/index.html), se existir."""
    index = settings.FRONTEND_DIST / 'index.html'
    if index.exists():
        return FileResponse(open(index, 'rb'), content_type='text/html')
    return HttpResponse(
        '<h1>NewFurniture API</h1>'
        '<p>O frontend roda em <a href="http://localhost:5173">http://localhost:5173</a> '
        '(cd frontend &amp;&amp; npm run dev).</p>'
        '<p>API navegável: <a href="/api/">/api/</a> · Admin: <a href="/admin/">/admin/</a></p>'
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api-auth/', include('rest_framework.urls')),  # login da API navegável
    re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': settings.FRONTEND_DIST / 'assets'}),
    re_path(r'^(?P<path>logo\.svg)$', serve, {'document_root': settings.FRONTEND_DIST}),
    path('', frontend_index),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

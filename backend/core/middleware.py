from django.http import HttpResponse


class CorsMiddleware:
    """CORS simples para desenvolvimento.

    Permite que o frontend React, rodando em outra porta (ex.: 5173), consuma a
    API. A autenticação é feita por token no cabeçalho Authorization (e não por
    cookie), por isso liberar qualquer origem é seguro neste contexto.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        preflight = (
            request.method == 'OPTIONS'
            and 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META
        )
        response = HttpResponse() if preflight else self.get_response(request)
        if request.path.startswith('/api/') or request.path.startswith('/media/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        return response

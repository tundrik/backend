import logging

import orjson
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.handlers.asgi import ASGIRequest
from django.http import HttpResponse

from base.bsv import ViewerType
from base.exceptions import JwtError, send_log
from base.JWT import decode_token
from base.response import HttpError
from storage.store import Store

logger = logging.getLogger('base.endpoint')


class Endpoint:
    """Базовый класс для всех конечных точек HTTP async."""
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self):
        self.payload = None
        self.viewer = None

    async def __call__(self, request, *args):
        pass

    @classmethod
    async def dispatch(cls, request: ASGIRequest, **kwargs):
        """
        Основная точка входа для процесса запрос-ответ
        1) Вызвать метод authenticate если требуется
        2) Попытайтесь отправить по правильному методу
        если метода не существует, передать обработчику ошибок.
        Также обратитесь к обработчику ошибок, если метода запроса нет в утвержденном списке.
        3) Установите payload если метод POST и application/json
        4) Установите guid
        5) Ловим неотловленные исключения
        """
        method = request.method.lower()
        self = cls()

        cls.set_viewer(self, request)

        access_level = kwargs.get('access_level')
        if access_level:
            await cls.authenticate(self, request, access_level)
            kwargs.pop('access_level')

        if method in cls.http_method_names:
            handler = getattr(cls, method, cls.http_method_not_allowed)
        else:
            handler = cls.http_method_not_allowed

        if method == 'post' and request.content_type == 'application/json':
            cls.parse_body(self, request.body)

        try:
            response = await handler(self, request, **kwargs)

        except Exception as exc:
            logger.critical(
                'Internal Server Error (%s): %s, Exception: %s', request.method, request.path, exc,
                extra={'status_code': 500, 'request': request}
            )
            await send_log(f'Internal Server Error: {exc}, {request.method} {request.path}')
            return HttpError(500, "500 Internal Server Error")

        return response

    async def authenticate(self, request, access_level):
        """
        Если есть валидный непросроченный токен с нужным уровнем доступа
            устанавливает в self.viewer объект Viewer
        иначе
            вызывает исключение PermissionDenied с 403 ошибкой в ответе
        """
        token = request.COOKIES.get('jwt_token')

        if token is None:
            raise PermissionDenied()

        try:
            person_dict = decode_token(token)

        except JwtError:
            raise PermissionDenied()

        if person_dict.get(access_level):
            self.viewer = ViewerType(**person_dict)
            has_blocked = await Store.get_blocked(self.viewer.pk)
            if has_blocked:
                raise PermissionDenied()
        else:
            raise PermissionDenied()

    def set_viewer(self, request):
        guid = request.COOKIES.get('GUID')
        self.viewer = ViewerType(
            pk=None,
            role=None,
            manager_id=None,
            guid=guid,
            internal=False
        )

    def parse_body(self, body):
        """Парсит body и устанавливает в self.payload"""
        try:
            self.payload = orjson.loads(body)

        except orjson.JSONDecodeError:

            raise SuspiciousOperation()

    async def http_method_not_allowed(self, request, **kwargs):
        """Обработка Method Not Allowed"""
        await send_log(f'Method Not Allowed: {request.method} {request.path}')
        response = HttpResponse(b'', status=405)
        response.headers['Allow'] = ', '.join(self._allowed_methods())
        return response

    async def options(self, request, **kwargs):
        """Обработка ответов на запросы HTTP-команды OPTIONS."""
        response = HttpResponse()
        response.headers['Allow'] = ', '.join(self._allowed_methods())
        response.headers['Content-Length'] = '0'
        return response

    @classmethod
    def _allowed_methods(cls):
        """Возвращает список поддерживаемых методов"""
        return [m.upper() for m in cls.http_method_names if hasattr(cls, m)]

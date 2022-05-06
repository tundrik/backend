import orjson
from django.http import HttpResponse


class OrjsonResponse(HttpResponse):
    def __init__(self, response_data) -> None:
        content = orjson.dumps(response_data)
        super().__init__(content=content, content_type='application/json', status=200)


class XmlResponse(HttpResponse):
    def __init__(self, response_data) -> None:
        super().__init__(content=response_data, content_type='application/xml', status=200)


class HttpError(HttpResponse):
    def __init__(self, status_code: int, message: str, has_json: bool = False) -> None:
        if not has_json:
            data = {
                "message": message
            }
            content = orjson.dumps(data)
        else:
            content = message
        super().__init__(content=content, content_type='application/json', status=status_code)


def no_data(request, exception=None):
    return HttpError(404, 'Нет данных по вашему запросу')


def forbidden(request, exception=None):
    return HttpError(403, '403 Forbidden')


def bad_request(request, exception=None):
    return HttpError(400, '400 Bad Request')

from base.helpers import generate_uuid


class ResponseHttpMiddleware:
    """
    Если нужно что-то сделать в конце цикла запрос ответ это подходящее место
    1) Добавляем в cookie GUID если еще нет
    2) Добавляем заголовки
    """
    sync_capable = False
    async_capable = True

    def __init__(self, get_response_async):
        self.get_response_async = get_response_async

    async def __call__(self, request):
        response = await self.get_response_async(request)
        host = request.META.get('HTTP_ORIGIN')
        response = self.set_header(response, host)
        cookie_guid = request.COOKIES.get('GUID')
        if cookie_guid is None:
            guid = generate_uuid()
            response.set_cookie(
                key='GUID',
                value=guid,
                max_age=365 * 24 * 60 * 60
            )
        return response

    @staticmethod
    def set_header(response, host):
        response["Access-Control-Allow-Origin"] = host
        response["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept, Authorization, " \
                                                   "Access-Control-Allow-Origin, Access-Control-Allow-Headers "
        response["Access-Control-Allow-Methods"] = "POST, PUT, GET, OPTIONS, DELETE"
        response["Access-Control-Allow-Credentials"] = "true"
        return response

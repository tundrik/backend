from base.exceptions import ThrottleError
from storage.store import Store


class Throttle:
    """
    Дроселирование запросов
    endpoint - конечная точка (по умолчанию 'all')
    identifier - строка идентификации, может быть (guid, ip, phone и т.д)
    allowed - количество разрешенных запросов (по умолчанию 1) в течении (duration по умолчанию 1 сек.)
    duration - секунд до удаления записи из redis

    сам по себе не чего не делает
    нужно вызвать метод use_throttle на запись
    и метод check_throttle для проверки
    вызывает exception ThrottleError
    """

    def __init__(
            self,
            endpoint: str = 'all',
            *,
            identifier,
            allowed: int = 1,
            duration: int = 1
    ):
        self.endpoint = endpoint
        self.identifier = identifier
        self.allowed = allowed
        self.duration = duration

    async def use_throttle(self):
        await Store.set_throttle(endpoints=self.endpoint, identifier=self.identifier, duration=self.duration)

    async def check_throttle(self):
        attempts, ttl = await Store.get_throttle(endpoints=self.endpoint, identifier=self.identifier)
        if attempts >= self.allowed:
            raise ThrottleError()

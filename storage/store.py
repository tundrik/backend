"""
TODO: Написать общий метод генерации ключей
"""
import time
import aioredis


class Store:
    """
    save:guid [values] - Сохраненные id обектов недвижимости ||expire
    pin:phone_number (has_create_person, pin) - Пин-код, Создать Person ??? ||expire
    throttle:endpoints:identifier - троттлинг ||expire
    status:phone_number_employee value - (on|off) - статус абонента риэлтора
    status:guid value - (on|off|focus) - статус экрана сайт/кабинет
    TODO: clicked_contact:phone_number_employee  guid | dict person | Purchase

    Потребности Телеграм бота:
        Был авторизован???
        Это риэлтор???
        Это клиент (покупатель??)
            Действующие подписки

    Потребности Сервиса звонков:
        В начале звонка:
            С нашего сайта???

            Есть информация???
        В конце звонка:
            Создать  Person, Customer, Purchase, Thread???
            
    """
    redis = aioredis.StrictRedis(decode_responses=True)

    @classmethod
    async def get_saved(cls, guid: str, types: str):
        key = "{}:{}:{}".format("save", types, guid)
        res = await cls.redis.zrange(key, 0, -1, withscores=False)
        ids = set(res)
        return ids

    @classmethod
    async def get_saved_score(cls, guid: str, types: str):
        key = "{}:{}:{}".format("save", types, guid)
        res = await cls.redis.zrange(key, 0, -1, withscores=True)
        ids_score = dict(res)
        ids = list(ids_score.keys())
        return ids, ids_score

    @classmethod
    async def toggle_save(cls, guid: str, identifier: str, types: str) -> bool:
        key = "{}:{}:{}".format("save", types, guid)
        res = await cls.redis.zrem(key, identifier)
        if not res:
            time_unix = int(time.time())
            res = await cls.redis.zadd(key, {identifier: time_unix})
        await cls.redis.expire(key, 1209600)
        return bool(res)

    @classmethod
    async def toggle_minus(cls, guid: str, target: str, pk: str) -> bool:
        key = "{}:{}".format("minus", target)
        res = await cls.redis.zrem(key, pk)
        if not res:
            time_unix = int(time.time())
            res = await cls.redis.zadd(key, {pk: time_unix})
            node_key = "{}:{}".format("minus", pk)
            target_res = await cls.redis.zadd(node_key, {target: time_unix})
        await cls.redis.expire(key, 7862400)
        return bool(res)

    @classmethod
    async def get_minus(cls, target: str):
        key = "{}:{}".format("minus", target)
        res = await cls.redis.zrange(key, 0, -1, withscores=False)
        return set(res)

    @classmethod
    async def set_pin_redis(cls, phone_number: int, pin: str) -> None:
        key = "{}:{}".format("pin", phone_number)
        await cls.redis.set(key, pin, ex=900)
        print(pin)

    @classmethod
    async def get_pin(cls, phone_number: int):
        key = "{}:{}".format("pin", phone_number)
        return await cls.redis.get(key)

    @classmethod
    async def set_throttle(cls, endpoints: str, identifier, duration: int) -> None:
        key = "{}:{}:{}".format("throttle", endpoints, identifier)
        await cls.redis.incr(key)
        await cls.redis.expire(key, duration)

    @classmethod
    async def get_throttle(cls, endpoints: str, identifier):
        ttl = 0
        key = "{}:{}:{}".format("throttle", endpoints, identifier)
        attempts = await cls.redis.get(key)
        if attempts:
            ttl = await cls.redis.ttl(key)
            attempts = int(attempts)
        else:
            attempts = 0
        return attempts, ttl

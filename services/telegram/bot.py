import asyncio
import httpx
import orjson
from constants import TELEGRAM_URL, WEBHOOK_TELEGRAM_HOST, WEBHOOK_TELEGRAM_PATH, MASTER_CHAT_ID, IS_WEBHOOK_TELEGRAM

from repository.query import query_employee


class TelegramService:
    """
    Сервис Телеграмм Бот
    """
    command_names = ['start']
    webhook_url = WEBHOOK_TELEGRAM_HOST + WEBHOOK_TELEGRAM_PATH
    client = httpx.AsyncClient(timeout=10, base_url=TELEGRAM_URL)
    instance = None

    def __init__(self):
        if IS_WEBHOOK_TELEGRAM:
            print("TelegramService __init__")
            asyncio.create_task(self.set_webhook())

    def __new__(cls):
        """
        Этот класс одиночка
        Нельзя полагаться на данные состояния при запуске с gunicorn процессами > 1
        хотя с --preload я не наблюдал создание классов но я до сих пор не уверен
        используйте для хранения данных
        1) redis
        2) multiprocessing.Manager ??
        """
        if cls.instance is None:
            cls.instance = super(TelegramService, cls).__new__(cls)
        return cls.instance

    async def __call__(self, scope, receive, send):
        """Не ждем handler, сразу возвращяем ответ 200"""
        print(self)
        receive_data = await receive()
        body_bytes = receive_data.get('body')
        asyncio.create_task(self._handler_webhook(body_bytes))
        await send({
            "type": "http.response.start",
            "status": 200,
        })
        await send({
            "type": "http.response.body",
        })

    async def set_webhook(self) -> None:
        """Просит присылать обновления на указанный адрес, не требует повтора"""
        data = dict(url=self.webhook_url)
        response = await self.client.post('/setWebhook', data=data)
        print(response.json())

    @classmethod
    async def send_message(cls, chat_id, send_text):
        """Отправляет сообщение"""
        data = dict(chat_id=chat_id, text=send_text)
        response = await cls.client.post('/sendMessage', data=data)
        print("send_message response", response.json())

    @classmethod
    async def get_user_profile_photos(cls, user_id: int):
        """
        Получить информацию о фотографиях профиля
        TODO: Написать получить ссылку на фото
        """
        data = dict(user_id=user_id)
        response = await cls.client.post('/getUserProfilePhotos', data=data)
        print("send_message response", response.json())

    @classmethod
    async def _forward_message(cls, from_chat_id: int, message_id: int) -> None:
        """Пересылает копию сообщения в MASTER_CHAT_ID для отслеживания ответов бота"""
        data = dict(chat_id=MASTER_CHAT_ID, from_chat_id=from_chat_id, message_id=message_id)
        await cls.client.post('/forwardMessage', data=data)

    @classmethod
    async def _send_chat_action(cls, chat_id: int, action: str = 'typing') -> None:
        """
        Используйте этот метод, когда ответ требует времени
        action:
        1) typing (...печатает)
        2) upload_photo (...отправляет фото)
        есть и другие
        """
        data = dict(chat_id=chat_id, action=action)
        response = await cls.client.post('/sendChatAction', data=data)
        print("send_chat_action", response.json())

    @classmethod
    async def _get_user_profile_contact(cls, chat_id: int) -> None:
        reply_markup = {
            "keyboard": [[{
                "text": "Поделится контактом",
                "request_contact": True
            }]],
            "one_time_keyboard": True,
            "resize_keyboard": True
        }
        reply_markup_json = orjson.dumps(reply_markup).decode("utf-8")

        data = dict(chat_id=chat_id, text='Поделитесь контактом', reply_markup=reply_markup_json)
        response = await cls.client.post('/sendMessage', data=data)
        print(response.json())

    @classmethod
    async def _handler_webhook(cls, body_bytes: bytes) -> None:
        """
        TODO: Отрефакторить после написания основного функционала
        :param body_bytes:
        :return:
        """
        body_dict = orjson.loads(body_bytes)
        message = body_dict.get('message')
        if message:
            text = message.get('text')
            contact = message.get('contact')
            chat_id = message['chat']['id']

            if contact:
                employee = await query_employee(contact.get('phone_number'), chat_id)
                if employee:
                    msg = "Готово"
                else:
                    msg = "Не найден сотрудник"
                asyncio.create_task(cls.send_message(chat_id=chat_id, send_text=msg))

            elif text == "/start":
                asyncio.create_task(cls._get_user_profile_contact(chat_id))

            else:
                msg = "Меня такому еще не научили"
                asyncio.create_task(cls.send_message(chat_id=chat_id, send_text=msg))

        print(body_dict)



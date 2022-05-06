from django.urls import resolve
from base.connection import WebSocket
from constants import WEBHOOK_TELEGRAM_PATH
from services.telegram.bot import TelegramService


class CoreRouter:
    def __init__(self, application):
        self.telegram_service = TelegramService()
        self.application = application

    async def __call__(self, scope, receive, send):
        is_http = scope['type'] == 'http'

        if scope['type'] == 'websocket':
            match = resolve(scope["path"])
            await match.func(WebSocket(scope, receive, send), *match.args, **match.kwargs)

        elif is_http and scope['path'] == WEBHOOK_TELEGRAM_PATH:
            await self.telegram_service(scope, receive, send)

        elif is_http:
            await self.application(scope, receive, send)

        else:
            raise NotImplementedError(f"Unknown scope type {scope['type']}")

import asyncio

from django.core.handlers.asgi import ASGIRequest

from base.endpoint import Endpoint
from base.helpers import decode_node_name
from base.response import OrjsonResponse
from services.telegram.bot import TelegramService
from storage.store import Store


class FeaturesApi(Endpoint):
    async def post(self, request: ASGIRequest, **kwargs):
        phone = request.POST.get("phone")
        name = request.POST.get("name")
        send_text_view = "Обращение по форме, {} {}".format(phone, name),
        telegram_chat_id = 786033449
        asyncio.create_task(TelegramService.send_message(chat_id=telegram_chat_id, send_text=send_text_view))
        return OrjsonResponse({
            'success': True,
        })


class ToggleFeatureApi(Endpoint):
    async def post(self, request: ASGIRequest, code_node=None):
        pk, type_node = decode_node_name(code_node)
        await Store.toggle_save(self.guid, pk, type_node)
        return OrjsonResponse({
            'success': True,
        })

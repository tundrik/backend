import asyncio

from constants import MASTER_CHAT_ID
from services.telegram.bot import TelegramService


async def send_log(log):
    # asyncio.create_task(TelegramService.send_message(chat_id=MASTER_CHAT_ID, send_text=log))
    pass


class InvalidCursor(Exception):
    pass


class ThrottleError(Exception):
    pass


class JwtError(Exception):
    pass


class NoData(Exception):
    pass


class ValidateError(Exception):
    pass


class AccessError(Exception):
    pass

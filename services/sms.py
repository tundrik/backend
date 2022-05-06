"""
TODO: Дописать проверку стоимости отправки смс
"""
import httpx

from constants import SMS_API_ID, SMS_TEST


async def send_sms(phone_number, send_text):
    params = {
        'api_id': SMS_API_ID,
        'to': 89654687130,
        'msg': send_text,
        'json': 1,
        'test': SMS_TEST
    }

    async with httpx.AsyncClient() as client:
        response = await client.get('https://sms.ru/sms/send', params=params)
        print(response.text)

import httpx
from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest

from base.JWT import generate_access_token
from base.endpoint import Endpoint
from base.exceptions import ValidateError
from base.helpers import generate_pin
from base.response import OrjsonResponse, HttpError
from domain.models import Employee
from mutation.validate import validate_phone
from services.telegram.bot import TelegramService
from storage.store import Store


class LoginApi(Endpoint):
    async def delete(self, request: ASGIRequest):
        print(self)
        response = OrjsonResponse({
                'success': True,
                'access_token': "",
        })
        response.delete_cookie('jwt_token')
        response.delete_cookie('GUID')
        return response

    async def post(self, request: ASGIRequest):
        phone = request.POST.get('phone')
        pin_for_checking = request.POST.get('pin')
        try:
            if pin_for_checking is None:
                return OrjsonResponse({
                    'success': True,
                    'message': await self.send_pin_code_telegram(phone),
                })
            else:
                access_token, guid = await self.check_pin_code(pin_for_checking, phone)
                response = OrjsonResponse({
                    'success': True,
                    'access_token': access_token,
                })
                response.set_cookie(
                    key='jwt_token',
                    value=access_token
                )
                response.set_cookie(
                    key='GUID',
                    value=guid,
                    max_age=365 * 24 * 60 * 60

                )
                return response

        except ValidateError as exc:
            return HttpError(400, str(exc))

    async def check_pin_code(self, pin_for_checking, phone):
        phone_number = validate_phone(phone)
        pin = await Store.get_pin(phone_number)

        if pin is None:
            raise ValidateError("Не найден пин код")

        if pin_for_checking != pin:
            raise ValidateError("Не верный PIN-код")

        employee = await self.query_employee_by_phone(phone_number)

        access_token = generate_access_token(employee)
        guid = employee.guid
        return access_token, guid

    async def send_pin_code_telegram(self, phone):
        phone_number = validate_phone(phone)
        pin = generate_pin()
        send_text_view = f'Ваш PIN-код {pin}'
        employee = await self.query_employee_by_phone(phone_number)

        if employee is None:
            raise ValidateError(f"Не найден сотрудник c номером <br />{phone}")

        telegram_chat_id = 786033449  # employee.telegram_chat_id

        if telegram_chat_id is None:
            raise ValidateError("Не найден телеграм чат, авторизуйтесь у Телеграм бота")

        try:
            await TelegramService.send_message(chat_id=telegram_chat_id, send_text=send_text_view)
            await Store.set_pin_redis(phone_number, pin)
            return f'PIN-код отправлен в телеграм {pin}'

        except httpx.ConnectTimeout:
            raise ValidateError("Не удалось отправить в телеграм попробуйте еще")

    @sync_to_async
    def query_employee_by_phone(self, phone_number):
        return Employee.objects.filter(phone=phone_number).first()


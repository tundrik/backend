from asgiref.sync import sync_to_async
from domain.models import Employee


@sync_to_async
def query_employee(phone_number, chat_id):
    return Employee.objects.filter(phone=phone_number).update(telegram_chat_id=chat_id)

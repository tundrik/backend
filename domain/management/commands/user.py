import time

from django.core.management import BaseCommand
from django.db import transaction

from base.helpers import generate_uuid
from domain.models import Employee


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        Employee.objects.create(
            first_name="максим",
            last_name="анохин",
            phone=79881607082,
            search_full="максим анохин 79881607082",
            telegram_chat_id=786033449,
            role="ADMIN",
            guid=generate_uuid(),
            ranging=int(time.time())
        )
        print("Done! ")

import time

from asgiref.sync import sync_to_async
from django.db import transaction

from base.bsv import Bsv
from base.exceptions import ValidateError
from base.helpers import generate_uuid
from domain.models import Employee, Customer, Demand, Location, Estate, EstateMedia, Project, ProjectMedia
from mutation.validate import (
    validate_employee, validate_demand,
    validate_customer, validate_location,
    validate_estate, validate_project
)


class CreateInspector(Bsv):
    async def add_node(self, *, type_node, pyload):
        handler = getattr(self, 'inspect_' + type_node)
        return await handler(pyload)

    async def inspect_demand(self, payload):
        customer = validate_customer(payload)
        demand = validate_demand(payload)
        await self.create_demand(demand, customer)

    async def inspect_estate(self, payload):
        address = payload.get("address")
        if not address:
            raise ValidateError("Введите адрес")

        images_names = payload.getlist('files')

        if len(images_names) < 4:
            raise ValidateError("Не менее 4 фотографий")

        customer = validate_customer(payload)
        estate = validate_estate(payload)

        location = await validate_location(payload)

        await self.create_estate(estate, customer, location, images_names)

    async def inspect_project(self, payload):
        print(payload)
        project = validate_project(payload)
        address = payload.get("address")
        if not address:
            raise ValidateError("Введите адрес")

        images_names = payload.getlist('files')

        if len(images_names) < 3:
            raise ValidateError("Не менее 3 фотографий")

        location = await validate_location(payload)

        await self.create_project(project, location, images_names)

    async def inspect_employee(self, payload):
        valid = validate_employee(payload)
        pic = payload.get("files")
        if pic:
            valid["pic"] = pic
        await self.create_employee(valid)

    @sync_to_async
    def create_employee(self, valid):
        Employee.objects.create(
            **valid,
            guid=generate_uuid(),
            ranging=int(time.time()),
        )

    @sync_to_async
    @transaction.atomic
    def create_demand(self, demand, customer):
        db_customer = Customer.objects.filter(phone=customer.get("phone")).first()
        if db_customer:
            if len(db_customer.first_name) < len(customer.get("first_name")):
                db_customer.first_name = customer.get("first_name")
                db_customer.save()
        else:
            db_customer = Customer.objects.create(
                guid=generate_uuid(),
                ranging=int(time.time()),
                **customer
            )

        Demand.objects.create(
            **demand,
            customer=db_customer,
            employee_id=self.viewer.pk,
            ranging=int(time.time()),
            published=int(time.time())
        )

    @sync_to_async
    def create_estate(self, estate, customer, location, images_names):
        db_customer = Customer.objects.filter(phone=customer.get("phone")).first()
        if db_customer:
            if len(db_customer.first_name) < len(customer.get("first_name")):
                db_customer.first_name = customer.get("first_name")
                db_customer.save()
        else:
            db_customer = Customer.objects.create(
                guid=generate_uuid(),
                ranging=int(time.time()),
                **customer
            )

        db_location = Location.objects.create(**location)
        for item in range(30):
            db_estate = Estate.objects.create(
                employee_id=self.viewer.pk,
                customer=db_customer,
                location=db_location,
                ranging=int(time.time()),
                published=int(time.time()),
                **estate
            )
            for index, name in enumerate(images_names):
                if name:
                    EstateMedia.objects.create(
                        estate=db_estate,
                        link=name,
                        ranging=index
                    )

    @sync_to_async
    @transaction.atomic
    def create_project(self, project, location, images_names):
        db_project = Project.objects.filter(project_name__iexact=project.get('project_name')).first()

        if db_project:
            raise ValidateError(f"{project.get('project_name')} уже существует")

        db_location = Location.objects.create(**location)

        db_project = Project.objects.create(
            location=db_location,
            employee_id=self.viewer.pk,
            published=int(time.time()),
            ranging=int(time.time()),
            **project
        )
        for index, name in enumerate(images_names):
            if name:
                ProjectMedia.objects.create(
                    project=db_project,
                    link=name,
                    ranging=index
                )

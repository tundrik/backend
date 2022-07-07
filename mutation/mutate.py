import time

from asgiref.sync import sync_to_async

from base.bsv import Bsv
from base.exceptions import ValidateError
from base.helpers import decode_node_name
from base.throttle import Throttle
from domain.models import Demand, Employee, Customer, Project, Estate, ProjectMedia, EstateMedia
from mutation.validate import validate_employee, validate_customer, validate_demand, validate_project, validate_estate
from storage.store import Store


class MutateInspector(Bsv):
    async def mutation_node(self, *, code_node, payload):
        pk, type_node = decode_node_name(code_node)
        handler = getattr(self, 'inspect_' + type_node)
        await handler(pk, payload)
        return type_node

    async def inspect_employee(self, pk, payload):
        employee = validate_employee(payload)
        if bool(payload.get('has_active')):
            await Store.delete_blocked(pk)
        else:
            await Store.set_blocked(pk)

        pic = payload.get("files")
        if pic:
            employee["pic"] = pic

        await self.mutation_employee(pk, employee)

    async def inspect_project(self, pk, payload):
        project = validate_project(payload)
        images_names = payload.getlist('files')

        if len(images_names) < 3:
            raise ValidateError("Не менее 3 фотографий")

        await self.mutation_project(pk, project, images_names)

    async def inspect_estate(self, pk, payload):
        customer = validate_customer(payload)
        estate = validate_estate(payload)
        images_names = payload.getlist('files')

        if len(images_names) < 4:
            raise ValidateError("Не менее 4 фотографий")

        db_customer = await self.get_customer(payload.get('customer_pk'))
        new_phone = customer.get('phone')
        if db_customer.phone != new_phone:
            throttle = Throttle('update_phone', identifier=self.viewer.pk, allowed=1, duration=20000)
            await throttle.check_throttle()
            await throttle.use_throttle()

        await self.mutation_estate(pk, estate, customer, images_names)

    async def inspect_demand(self, pk, payload):
        customer = validate_customer(payload)
        demand = validate_demand(payload)

        db_customer = await self.get_customer(payload.get('customer_pk'))
        new_phone = customer.get('phone')
        if db_customer.phone != new_phone:
            throttle = Throttle('update_phone', identifier=self.viewer.pk, allowed=1, duration=20000)
            await throttle.check_throttle()
            await throttle.use_throttle()

        await self.mutation_demand(pk, demand, customer)

    @sync_to_async
    def mutation_employee(self, pk, employee):
        Employee.objects.filter(pk=pk).update(**employee)

    @sync_to_async
    def mutation_project(self, pk, project, images_names):
        Project.objects.filter(pk=pk).update(**project, ranging=int(time.time()))
        db_project = Project.objects.get(pk=pk)
        for index, name in enumerate(images_names):
            if name:
                try:
                    obj, created = ProjectMedia.objects.update_or_create(
                        link=name, project=db_project, defaults={"ranging": index, 'project': db_project}
                    )
                except ProjectMedia.MultipleObjectsReturned as exc:
                    print(exc)

    @sync_to_async
    def mutation_estate(self, pk, estate, customer, images_names):
        db_estate = Estate.objects.get(pk=pk)

        customer_id = db_estate.customer_id
        Customer.objects.filter(pk=customer_id).update(**customer)

        Estate.objects.filter(pk=pk).update(**estate, ranging=int(time.time()))
        for index, name in enumerate(images_names):
            if name:
                try:
                    obj, created = EstateMedia.objects.update_or_create(
                        link=name, estate=db_estate, defaults={"ranging": index, 'estate': db_estate}
                    )
                except EstateMedia.MultipleObjectsReturned as exc:
                    print(exc)

    @sync_to_async
    def mutation_demand(self, pk, demand, customer):
        Demand.objects.filter(pk=pk).update(**demand, ranging=int(time.time()))
        db_demand = Demand.objects.get(pk=pk)
        Customer.objects.filter(pk=db_demand.customer_id).update(**customer)

    @sync_to_async
    def get_customer(self, customer_pk):
        return Customer.objects.get(pk=customer_pk)

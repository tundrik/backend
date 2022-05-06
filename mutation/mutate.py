from asgiref.sync import sync_to_async

from base.bsv import Bsv
from base.helpers import decode_node_name
from domain.models import Demand, Employee, Customer, Project, Estate
from mutation.validate import validate_employee, validate_customer, validate_demand, validate_project, validate_estate
from services.yandex.s3 import YandexUploader


class MutateInspector(Bsv):
    async def mutation_node(self, *, code_node, payload, files):
        pk, type_node = decode_node_name(code_node)
        handler = getattr(self, 'inspect_' + type_node)
        await handler(pk, payload, files)
        return type_node

    async def inspect_employee(self, pk, payload, files):
        image = files.get('image')
        employee = validate_employee(payload)

        if image:
            pic_name = await self.get_pic(pk)
            async with YandexUploader() as uploader:
                employee["pic"] = await uploader.profile_upload(image)
                if not pic_name == 'User':
                    await uploader.delete_image(name=pic_name, width="profile")

        await self.mutation_employee(pk, employee)

    async def inspect_project(self, pk, payload, files):
        project = validate_project(payload)
        await self.mutation_project(pk, project)

    async def inspect_estate(self, pk, payload, files):
        customer = validate_customer(payload)
        estate = validate_estate(payload)
        await self.mutation_estate(pk, estate, customer)

    async def inspect_demand(self, pk, payload, files):
        customer = validate_customer(payload)
        demand = validate_demand(payload)
        await self.mutation_demand(pk, demand, customer)

    @sync_to_async
    def get_pic(self, pk):
        employee = Employee.objects.filter(pk=pk).first()
        return employee.pic

    @sync_to_async
    def mutation_employee(self, pk, employee):
        Employee.objects.filter(pk=pk).update(**employee)

    @sync_to_async
    def mutation_project(self, pk, project):
        Project.objects.filter(pk=pk).update(**project)

    @sync_to_async
    def mutation_estate(self, pk, estate, customer):
        db_estate = Estate.objects.get(pk=pk)
        customer_id = db_estate.customer_id
        Customer.objects.filter(pk=customer_id).update(**customer)
        Estate.objects.filter(pk=pk).update(**estate)

    @sync_to_async
    def mutation_demand(self, pk, demand, customer):
        Demand.objects.filter(pk=pk).update(**demand)
        db_demand = Demand.objects.get(pk=pk)
        Customer.objects.filter(pk=db_demand.customer_id).update(**customer)

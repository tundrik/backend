from asgiref.sync import sync_to_async
from django.db import IntegrityError

from base.bsv import Bsv
from base.exceptions import AccessError
from base.helpers import decode_node_name
from domain.models import Demand, Customer, Project, Estate, EstateMedia, ProjectMedia, EstateKit
from services.yandex.s3 import YandexUploader


class DeleteInspector(Bsv):
    async def delete_node(self, *, code_node):
        pk, type_node = decode_node_name(code_node)
        handler = getattr(self, 'delete_' + type_node)
        await handler(pk)

    @sync_to_async
    def delete_employee(self, pk):
        raise AccessError()

    @sync_to_async
    def delete_kit(self, pk):
        kit = EstateKit.objects.get(pk=pk)
        if self.viewer.pk != kit.employee_id:
            raise AccessError()
        kit.delete()

    @sync_to_async
    def delete_demand(self, pk):
        demand = Demand.objects.get(pk=pk)
        if self.viewer.pk != demand.employee_id:
            raise AccessError()
        customer = Customer.objects.get(pk=demand.customer_id)
        demand.delete()
        try:
            customer.delete()
        except IntegrityError as e:
            print("ProtectedError", e)

    async def delete_estate(self, pk):
        await self.delete_images(await self.query_estate_images(pk))
        await self.delete_db_estate(pk)

    async def delete_project(self, pk):
        await self.delete_images(await self.query_project_images(pk))
        await self.delete_db_project(pk)

    @sync_to_async
    def delete_db_estate(self, pk):
        estate = Estate.objects.get(pk=pk)
        if self.viewer.pk != estate.employee_id:
            raise AccessError()
        estate.delete()
        customer = Customer.objects.get(pk=estate.customer_id)
        try:
            customer.delete()
        except IntegrityError as e:
            print("ProtectedError", e)

    @sync_to_async
    def delete_db_project(self, pk):
        project = Project.objects.get(pk=pk)
        project.delete()

    @sync_to_async
    def query_estate_images(self, pk):
        images = EstateMedia.objects.filter(estate_id=pk)
        return list(images)

    @sync_to_async
    def query_project_images(self, pk):
        images = ProjectMedia.objects.filter(project_id=pk)
        return list(images)

    @staticmethod
    async def delete_images(images):
        async with YandexUploader() as uploader:
            for image in images:
                await uploader.delete_image(name=image.link, width="420")
                await uploader.delete_image(name=image.link, width="1200")

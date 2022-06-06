import asyncio

from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest

from base.endpoint import Endpoint
from base.exceptions import ValidateError, AccessError, ThrottleError
from base.response import OrjsonResponse, HttpError
from domain.models import Employee, ProjectMedia, EstateMedia
from mutation.create import CreateInspector
from mutation.delete import DeleteInspector
from repository.form import FormRepository
from mutation.mutate import MutateInspector
from services.yandex.s3 import YandexUploader


class UploadApi(Endpoint):
    async def post(self, request: ASGIRequest, type_node=None):
        file = request.FILES.get('files')
        print(file)
        async with YandexUploader() as uploader:
            if type_node == 'employee':
                image_name = await uploader.profile_upload(file)
            else:
                image_name = await uploader.image_upload(file)
        return OrjsonResponse({
            'success': True,
            'message': image_name,
        })


class MediaApi(Endpoint):
    async def post(self, request: ASGIRequest, type_node=None):
        server_id = request.POST.get("server_id")
        async with YandexUploader() as uploader:
            if type_node == 'employee':
                await uploader.delete_image(name=server_id, width="profile")
                await self.pic_employee_delete(server_id)
            else:
                await uploader.delete_image(name=server_id, width="420")
                await uploader.delete_image(name=server_id, width="1200")
                if type_node == 'project':
                    await self.pic_project_delete(server_id)
                if type_node == 'estate':
                    await self.pic_estate_delete(server_id)

        return OrjsonResponse({
            'success': True,
            'message': "image_name",
        })

    @sync_to_async
    def pic_employee_delete(self, server_id):
        Employee.objects.filter(pic=server_id).update(pic="User")

    @sync_to_async
    def pic_project_delete(self, server_id):
        media = ProjectMedia.objects.filter(link=server_id)
        for image in list(media):
            image.delete()

    @sync_to_async
    def pic_estate_delete(self, server_id):
        media = EstateMedia.objects.filter(link=server_id)
        for image in list(media):
            image.delete()


class AddApi(Endpoint):
    async def post(self, request: ASGIRequest, type_node=None):
        """Добавить (employee|estate|project|demand)"""
        inspection = CreateInspector(viewer=self.viewer)
        try:
            await inspection.add_node(type_node=type_node, pyload=request.POST)
            return OrjsonResponse({
                'success': True,
                'message': "Успешно создано",
                'type_node': type_node
            })

        except ValidateError as exc:
            return HttpError(400, str(exc))


class DeleteApi(Endpoint):
    async def post(self, request: ASGIRequest, code_node=None):
        """удалить (employee|estate|project|demand|kit)"""
        inspection = DeleteInspector(viewer=self.viewer)
        try:
            await inspection.delete_node(code_node=code_node)
            return OrjsonResponse({
                'success': True,
                'message': "Успешно удалено",
            })
        except AccessError:
            return HttpError(409, "Нет доступа")


class UpdateApi(Endpoint):
    async def get(self, request: ASGIRequest, code_node=None):
        """Вернуть форму (employee|estate|project|demand) на редактирование"""
        repository = FormRepository(viewer=self.viewer)
        response_data = await repository.retrive_node(code_node=code_node)
        return OrjsonResponse(response_data)

    async def post(self, request: ASGIRequest, code_node=None):
        """обновить (employee|estate|project|demand)"""
        inspection = MutateInspector(viewer=self.viewer)
        try:
            type_node = await inspection.mutation_node(code_node=code_node, payload=request.POST)
            return OrjsonResponse({
                'success': True,
                'message': "Успешно изменино",
                'type_node': type_node
            })

        except ValidateError as exc:
            return HttpError(400, str(exc))

        except ThrottleError:
            return HttpError(400, "Превышен лимит запросов на изменение номера")

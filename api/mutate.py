import asyncio

from django.core.handlers.asgi import ASGIRequest

from base.endpoint import Endpoint
from base.exceptions import ValidateError, AccessError
from base.response import OrjsonResponse, HttpError
from mutation.create import CreateInspector
from mutation.delete import DeleteInspector
from repository.form import FormRepository
from mutation.mutate import MutateInspector


class AddApi(Endpoint):
    async def post(self, request: ASGIRequest, type_node=None):
        """Добавить (employee|estate|project|demand)"""
        inspection = CreateInspector(viewer=self.viewer)
        try:
            await inspection.add_node(type_node=type_node, pyload=request.POST, files=request.FILES)
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
            type_node = await inspection.mutation_node(code_node=code_node, payload=request.POST, files=request.FILES)
            return OrjsonResponse({
                'success': True,
                'message': "Успешно изменино",
                'type_node': type_node
            })

        except ValidateError as exc:
            return HttpError(400, str(exc))


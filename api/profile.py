import time

from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest

from base.exceptions import NoData
from base.helpers import decode_node_name, encode_node_name
from base.response import no_data, OrjsonResponse, HttpError
from base.endpoint import Endpoint
from base.helpers import get_full_name, phone_number_to_string
from constants import PIC_BASE
from repository.navigator import NavigatorRepository
from domain.models import Employee, EstateKit, EstateKitMember


class ViewerApi(Endpoint):
    async def get(self, request: ASGIRequest):
        person = await self.query_viewer(self.viewer.pk)
        return OrjsonResponse({
            'person': {
                'pic': "{}{}.jpeg".format(PIC_BASE, person.pic),
                'name': get_full_name(person),
                'phone': phone_number_to_string(person.phone),
            },
        })

    @sync_to_async
    def query_viewer(self, pk):
        return Employee.objects.get(pk=pk)


class SavedApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        saved = await self.query_saved()
        response_data = {}
        for kit_member in saved:
            response_data[encode_node_name(kit_member.estate_id, "estate")] = True
        return OrjsonResponse(response_data)

    @sync_to_async
    def query_saved(self):
        return list(EstateKitMember.objects.filter(kit__employee_id=self.viewer.pk))


class DeleteSavedApi(Endpoint):
    async def post(self, request: ASGIRequest, code_node=None):
        await self.delete_saved(code_node)
        response_data = {}
        return OrjsonResponse(response_data)

    @sync_to_async
    def delete_saved(self, code_node):
        pk, type_node = decode_node_name(code_node)
        EstateKitMember.objects.filter(kit__employee_id=self.viewer.pk, estate_id=pk).delete()


class KitMembersApi(Endpoint):
    async def get(self, request: ASGIRequest, code_node=None):
        pk, type_node = decode_node_name(code_node)
        repository = NavigatorRepository(viewer=self.viewer)
        try:
            response_data = await repository.retrieve_kit_members(pk=pk)
            return OrjsonResponse(response_data)
        except NoData:
            return no_data(request)


class KitApi(Endpoint):
    async def post(self, request: ASGIRequest, **kwargs):
        node_code = request.POST.get("node")
        estate_pk, type_node = decode_node_name(node_code)

        for name, selected in request.POST.items():
            if selected == "on":
                pk_kit, type_node = decode_node_name(name)
                await self.add_kit_members(pk_kit, estate_pk)

        kit_name = request.POST.get("new_kit")

        response = None
        if kit_name:
            pk_new_kit = await self.add_kit(kit_name)
            await self.add_kit_members(pk_new_kit, estate_pk)
            response = {
                "kit_name": kit_name,
                "node_type": "kit",
                "node_code": encode_node_name(pk_new_kit, "kit")
            }
        return OrjsonResponse({
            'success': True,
            'new_kit': response,
        })

    async def get(self, request: ASGIRequest, **kwargs):
        entities = await self.query_kits()
        edges = []
        for entity in entities:
            edges.append({
                "kit_name": entity.kit_name,
                "node_type": "kit",
                "node_code": encode_node_name(entity.id, "kit")
            })
        return OrjsonResponse({
            'edges': edges,
        })

    @sync_to_async
    def add_kit(self, kit_name):
        kit = EstateKit.objects.create(
            employee_id=self.viewer.pk,
            kit_name=kit_name
        )
        return kit.pk

    @sync_to_async
    def add_kit_members(self, kit_pk, estate_pk):
        EstateKitMember.objects.create(
            kit_id=kit_pk,
            estate_id=estate_pk,
            ranging=int(time.time()),
        )

    @sync_to_async
    def query_kits(self):
        return list(EstateKit.objects.all())

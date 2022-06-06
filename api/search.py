import httpx
import orjson
from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest

from base.endpoint import Endpoint
from base.helpers import get_full_name
from base.response import OrjsonResponse
from domain.models import Project, Employee


class SuggestionsApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Token 21007033911dd578bd3a4379802c5d7a1b907753'
        }
        data = orjson.dumps({
            "query": request.GET.get("g"),
            "locations": [{
                "city": "сочи"
            }]
        })
        suggestions = []
        async with httpx.AsyncClient(timeout=None) as client:
            res = await client.post(url, headers=headers, data=data)
            content = orjson.loads(res.content)
            for item in content.get('suggestions'):
                print(item)

                data = item.get("data")
                lat = data.get("geo_lat")
                lng = data.get("geo_lon")
                street_type = data.get("street_type_full")
                if not street_type:
                    street_type = data.get("settlement_type_full")

                street = data.get("street")
                if not street:
                    street = data.get("settlement")

                if data.get("house"):
                    house = ", дом {}".format(data.get("house"))
                else:
                    house = ""

                value = "{} {}{}".format(street_type, street, house)

                data_object = {
                    "lat": lat,
                    "lng": lng,
                    "street_type": street_type,
                    "street": street,
                    "house": house,
                    "value": value
                }
                suggestions.append(data_object)

        return OrjsonResponse(suggestions)


class ProjectApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        query = request.GET.get("g")
        entities = await self.query_progect(query)
        edges = []
        for entity in entities:
            edges.append({
                "value": entity.project_name,
                "id": entity.id
            })
        return OrjsonResponse(edges)

    @sync_to_async
    def query_progect(self, query):
        qs = Project.objects.filter(project_name__trigram_word_similar=query)
        return list(qs)


class ManagerApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        entities = await self.query_manager()
        edges = []
        for entity in entities:
            edges.append({
                "label": get_full_name(entity),
                "value": entity.id
            })
        return OrjsonResponse(edges)

    @sync_to_async
    def query_manager(self):
        qs = Employee.objects.filter(role="mini_boss")
        return list(qs)


class TestApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        address = request.GET.get("g")
        base_url = "https://geocode-maps.yandex.ru/1.x"
        apikey = "8e802446-42a3-4c58-9137-da5007e86ae7"
        params = {
            "geocode": address,
            "apikey": apikey,
            "format": "json",
            "results": 1
        }
        valid = {}
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.get(base_url, params=params)
            parsed = orjson.loads(response.text)

        feature_members = parsed["response"]["GeoObjectCollection"]["featureMember"]
        if feature_members:

            geo_object = feature_members[0]["GeoObject"]
            address_2 = geo_object["metaDataProperty"]["GeocoderMetaData"]["text"]
            point = geo_object["Point"]["pos"].split()
            components = geo_object["metaDataProperty"]["GeocoderMetaData"]["Address"]["Components"]
            valid["lat"] = point[0]
            valid["lng"] = point[1]
            for component in components:
                if component.get("kind") == "district":
                    valid["district"] = component.get("name")
                if component.get("kind") == "locality":
                    valid["locality"] = component.get("name")
        return OrjsonResponse({"suggestions": address_2, "re": feature_members})


class MirabaseApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        print(self)
        base_url = "http://api.mirabase.ru/ap2/External/primary/list"
        data = {'login': "liberty", 'password': 'Z3Bk'}
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(base_url, data=data)
            parsed = orjson.loads(response.text)
            print(response)

        return OrjsonResponse({"parsed": parsed})


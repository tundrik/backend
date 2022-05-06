import httpx
import orjson
from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest

from base.endpoint import Endpoint
from base.response import OrjsonResponse
from domain.models import Project


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
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, data=data)
            response_data = orjson.loads(res.content)
        return OrjsonResponse(response_data)


class ProjectApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        query = request.GET.get("g")
        entities = await self.query_progect(query)
        edges = []
        for entity in entities:
            edges.append({
                "value": entity.project_name,
                "project_id": entity.id
            })
        return OrjsonResponse({"suggestions": edges})

    @sync_to_async
    def query_progect(self, query):
        qs = Project.objects.filter(project_name__trigram_word_similar=query)
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


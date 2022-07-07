import asyncio
import httpx
import orjson
from io import BytesIO
from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest

from base.endpoint import Endpoint
from base.exceptions import send_log
from base.helpers import get_full_name
from base.response import OrjsonResponse
from domain.models import Project, Employee, Location, ProjectMedia
from services.yandex.s3 import YandexUploader


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
    @sync_to_async
    def create_project(self, project):
        location = project.get("location")
        images_names = project.get("images_names")
        project = project.get("project")
        db_location = Location.objects.create(**location)
        db_project = Project.objects.create(
            location=db_location,
            employee_id=2,
            **project
        )
        for index, name in enumerate(images_names):
            if name:
                ProjectMedia.objects.create(
                    project=db_project,
                    link=name,
                    ranging=index
                )

    async def get(self, request: ASGIRequest, **kwargs):
        asyncio.create_task(self.task())
        return OrjsonResponse({
            "folow": "folow",
            "folow2": "folow2"
        })

    async def task(self):
        buildings_ids = []
        headers = {
            'x-api-token': 'ZGJ6MTRXVUpWNjBOaFNXNno4L0NoQT09',
            'content-type': 'application/json'
        }
        data = {
            "deadlineEnd": False,
            "orderDirection": "DESC",
            "region": ["1", "2", "3", "4", "5", "6"],
            "orderField": "date_update",
            "userUid": "f6004ae67280c339c0e66ad7dd09e6f7",
        }
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post("https://api.nedvx.ru/buildings/search", json=data, headers=headers)
            buildings = orjson.loads(response.text)
            data_nedvex = buildings.get("data")
            rows = data_nedvex.get("rows")
            for row in rows:
                black_list = row.get("black_list")
                if not black_list:
                    buildings_ids.append(row.get("id"))

            for buildings_id in buildings_ids:
                await asyncio.sleep(1)
                try:
                    params = {
                        "id": buildings_id,
                        "userUid": "f6004ae67280c339c0e66ad7dd09e6f7",
                    }
                    response2 = await client.get("https://api.nedvx.ru/buildings/get", params=params, headers=headers)
                    build = orjson.loads(response2.text)
                    build_parse = build.get("data")
                    address = build_parse.get("address")
                    region = build_parse["region"]["name"]
                    subregion = build_parse["subregion"]["name"]

                    address_split = address.split(",")
                    if address.startswith('Россия'):
                        house = address_split[-1]
                        street = address_split[-2]
                    else:
                        house = address_split[1]
                        street = address_split[0]

                    project_name = build_parse.get("title")

                    if project_name.startswith('АК'):
                        type_enum = "АК"
                    elif project_name.startswith('КП'):
                        house = ""
                        type_enum = "КП"

                    elif project_name.startswith('ТХ'):
                        house = ""
                        type_enum = "КП"

                    else:
                        type_enum = "ЖК"

                    house_territory = build_parse.get("house_territory")
                    if house_territory == "Закрытая":
                        has_closed_area = True
                    else:
                        has_closed_area = False

                    supple = {
                        "has_closed_area": has_closed_area,
                        "has_lift": True,
                        "has_rubbish_chute": False,
                    }

                    location = {
                        "lat": build_parse.get("latitude"),
                        "lng": build_parse.get("longitude"),
                        "address": address,
                        "street": street,
                        "locality": region,
                        "district": subregion,
                        "house": house,
                        "floors": 3,
                        "supple": supple,
                    }

                    pavilions = build_parse.get("pavilions")[0]
                    min_area_cost = pavilions.get("min_area_cost")
                    cost_min = pavilions.get("cost_min")

                    if cost_min:
                        price = int(cost_min)
                    else:
                        price = 8000000

                    if min_area_cost:
                        price_square = int(min_area_cost)
                    else:
                        price_square = 120000

                    min_square = build_parse.get("min_square")
                    if min_square:
                        square = int(float(min_square))
                    else:
                        square = 30

                    project = {
                        "project_name": project_name,
                        "type_enum": type_enum,
                        "published": build_parse.get("created"),
                        "ranging": build_parse.get("update"),
                        "comment": build_parse.get("description"),
                        "price": price,
                        "square": square,
                        "price_square": price_square,
                    }

                    album = build_parse["albums"]["rows"][0]

                    images = album.get("images")
                    image_names = []

                    for image in images[:18]:
                        image_id = image.get("id")
                        image_url = "https://api.nedvx.ru/image?id=" + str(image_id) + "&size=1200x800"
                        r = await client.get(image_url)
                        file = BytesIO(r.content)
                        async with YandexUploader() as uploader:
                            image_name = await uploader.image_upload(file)
                        image_names.append(image_name)

                    valid = {
                        "location": location,
                        "project": project,
                        "images_names": image_names,
                    }
                    await self.create_project(valid)

                except Exception as exc:
                    await send_log(f'NEDVEX: {exc}')






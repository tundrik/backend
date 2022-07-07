import asyncio
import time
from io import BytesIO

import httpx
import orjson
from asgiref.sync import sync_to_async
from django.core.management import BaseCommand

from base.exceptions import send_log
from domain.models import Location, ProjectMedia, Project
from services.yandex.s3 import YandexUploader


class Command(BaseCommand):

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

    def handle(self, *args, **options):
        asyncio.run(self.task())

    async def task(self):
        buildings_ids = []
        count = 0
        headers = {
            'x-api-token': 'YXVJV1NwdmdHWUtzMm04bE1mWE5pZz09',
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
                await asyncio.sleep(3)
                try:
                    count += 1
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
                        "nedvex_id": buildings_id,
                        "project_name": project_name,
                        "type_enum": type_enum,
                        "published": build_parse.get("created"),
                        "ranging": build_parse.get("created"),
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
                    print(count)

                except Exception as exc:
                    print(exc)

        print("Done! ")

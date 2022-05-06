import json

import httpx
from django.core.management import BaseCommand
from django.db import transaction

from domain.models import Project, Location


class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):
        res = httpx.get('https://onyx-realty.ru/kabinet/public-api/v1/mig/items/apartments/', timeout=None)
        projects = json.loads(res.content)
        for item in projects:

            project = Project.objects.create(
                mirabase_id=item['id'],
                link_part=item['shortcode'],

                type_enum="ЖК",
                name=item['name'],

                price=item['cost.mincost'],
                square=int(item['cost.minsq']),
                price_square=int(item['cost.mincost']) / int(item['cost.minsq']),
                comment=item['property_description'],

                media_video=item['media_video'],

                deadline=item['deadline'],

                ranging=item['ranging'],
                published=item['ranging'],
            )
            Location.objects.create(
                project=project,
                type_enum="ЖК",
                supple={
                    'has_covered_parking': False,
                    'has_lift': False,
                    'has_closed_area': False,
                    'floors': 1,
                },

                address=address,
                area=item['area'],
                micro_area=item['micro_area'],
                street=item['street'],
                house_number=item['house'],

            )

        print("Done! ")

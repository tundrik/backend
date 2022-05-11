from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest

import datetime
from xml.etree.ElementTree import Element, tostring

from base.endpoint import Endpoint
from base.helpers import get_full_name, phone_number_to_string
from base.response import XmlResponse
from constants import PRESENTATION_BASE, PIC_BASE
from domain.models import Estate, GROUND, HOUSE, RESIDENTIAL, COMMERCIAL


def add_filed(ad, filed, text):
    filed = Element(filed)
    filed.text = str(text)
    ad.append(filed)


@sync_to_async
def query_estate(params):
    qs = Estate.objects.filter(**params) \
        .prefetch_related('media') \
        .prefetch_related('location') \
        .prefetch_related('employee')
    return list(qs)


CATEGORY_AVITO = {
    "residential": 'Квартиры',
    "house": 'Дома, дачи, коттеджи',
    "ground": 'Земельные участки',
    "commercial": 'Коммерческая недвижимость',
}

CATEGORY_YANDEX = {
    "residential": 'flat',
    "house": 'house with lot',
    "ground": 'lot',
    "commercial": 'commercial',
}

CATEGORY_CIAN = {
    "residential": 'flatSale',
    "house": 'houseSale',
    "ground": 'landSale',
    "commercial": 'freeAppointmentObjectSale',
}


OBJECT_AVITO = {
    0: '',
    1: '',
    2: '',
    3: '',
    4: 'Дом',
    5: 'Дача',
    6: 'Коттедж',
    7: 'Таунхаус',
    8: 'Поселений (ИЖС)',
    9: 'Сельхозназначения (СНТ, ДНП)',
    10: 'Промназначения',
    11: 'Гостиница',
    12: 'Офисное помещение',
    13: 'Помещение общественного питания',
    14: 'Помещение свободного назначения',
    15: 'Производственное помещение',
    16: 'Складское помещение',
    17: 'Торговое помещение',
    18: 'Автосервис',
    19: 'Здание',
}

RENOVATION_AVITO = {
    "1": 'Требуется',
    "2": 'Косметический',
    "3": 'Евро',
    "4": 'Дизайнерский',
}

RENOVATION_YANDEX = {
    "1": 'требует ремонта',
    "2": 'косметический',
    "3": 'евроремонт',
    "4": 'дизайнерский',
}


ROOMS_AVITO = {
    12: 'Свободная планировка',
    1: 1,
    2: 2,
    3: 3,
    4: 4,
}

ROOMS_YANDEX = {
    0: 1,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
}

ROOMS_CIAN = {
    0: 7,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
}


class AvitoApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        root = Element("Ads", formatVersion="3", target="Avito.ru")
        edges = await query_estate({"has_avito": True})
        for estate in edges:
            ad = Element("Ad")
            add_filed(ad, 'id', estate.id)
            add_filed(ad, 'ManagerName', get_full_name(estate.employee))
            add_filed(ad, 'ContactPhone', phone_number_to_string(estate.employee.phone))

            add_filed(ad, 'Address', "Россия, " + estate.location.address)

            add_filed(ad, 'Latitude', estate.location.lat)
            add_filed(ad, 'Longitude', estate.location.lng)

            add_filed(ad, 'Description', estate.comment)
            add_filed(ad, 'Category', CATEGORY_AVITO.get(estate.type_enum))
            add_filed(ad, 'OperationType', "Продам")
            add_filed(ad, 'Price', estate.price)

            add_filed(ad, 'Rooms', ROOMS_AVITO.get(estate.rooms))

            if not estate.type_enum == GROUND:
                add_filed(ad, 'Square', estate.square)

            if estate.type_enum == HOUSE or estate.type_enum == GROUND:
                add_filed(ad, 'LandArea', estate.square_ground)

            if estate.type_enum == RESIDENTIAL or estate.type_enum == COMMERCIAL:
                add_filed(ad, 'Floor', estate.floor)

            if not estate.type_enum == GROUND:
                add_filed(ad, 'Floors', estate.location.floors)

            if estate.type_enum == RESIDENTIAL:
                add_filed(ad, 'HouseType', "Монолитный")

            if estate.type_enum == HOUSE:
                add_filed(ad, 'WallsType', "Газоблоки")

            add_filed(ad, 'MarketType', "Вторичка")
            add_filed(ad, 'PropertyRights', "Посредник")

            if not estate.type_enum == RESIDENTIAL:
                add_filed(ad, 'ObjectType', OBJECT_AVITO.get(estate.object_type))

            if estate.type_enum == RESIDENTIAL or estate.type_enum == COMMERCIAL:
                add_filed(ad, 'Decoration', 'Чистовая')

            if estate.type_enum == RESIDENTIAL:
                add_filed(ad, 'Status', "Квартира")
                lift = estate.location.supple.get("has_lift")
                if lift:
                    passenger_elevator = "1"
                else:
                    passenger_elevator = "нет"

                add_filed(ad, 'PassengerElevator', passenger_elevator)

            if estate.type_enum == RESIDENTIAL or estate.type_enum == HOUSE:
                renovation = estate.supple.get("renovation", "1")
                add_filed(ad, 'Renovation', RENOVATION_AVITO.get(renovation))

            if estate.type_enum == RESIDENTIAL:
                room_type = Element("RoomType")
                add_filed(room_type, 'Option', 'Изолированные')
                ad.append(room_type)

            if estate.type_enum == HOUSE:
                add_filed(ad, 'LandStatus', 'Индивидуальное жилищное строительство (ИЖС)')

            images_feed = Element("Images")
            for media_image in estate.media.all():
                image_feed = Element("Image", url="{}{}.jpeg".format(PRESENTATION_BASE, media_image.link))
                images_feed.append(image_feed)

            ad.append(images_feed)

            add_filed(ad, 'DealType', "Прямая продажа")
            add_filed(ad, 'PropertyRights', "Посредник")

            root.append(ad)

        return XmlResponse(tostring(root, encoding="UTF-8", xml_declaration=True))


class YandexApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        root = Element("realty-feed", xmlns="http://webmaster.yandex.ru/schemas/feed/realty/2010-06")
        add_filed(root, 'generation-date', datetime.datetime.now().astimezone().replace(microsecond=0).isoformat())

        edges = await query_estate({"has_yandex": True})
        for estate in edges:
            internal_id = {'internal-id': str(estate.id)}
            ad = Element("offer", **internal_id)
            add_filed(ad, 'type', 'продажа')
            add_filed(ad, 'property-type', 'жилая')
            add_filed(ad, 'deal-status', 'sale')

            add_filed(ad, 'category', CATEGORY_YANDEX.get(estate.type_enum))
            add_filed(ad, 'creation-date', datetime.datetime.fromtimestamp(estate.published).isoformat() + "+03:00")

            location = Element("location")
            add_filed(location, 'country', 'Россия')
            add_filed(location, 'region', 'Краснодарский край')
            add_filed(location, 'district', estate.location.district)
            add_filed(location, 'locality-name', estate.location.locality)
            add_filed(location, 'address', "{} {}, {}".format(
                estate.location.street_type,
                estate.location.street,
                estate.location.house
            ))
            add_filed(location, 'latitude', estate.location.lat)
            add_filed(location, 'longitude', estate.location.lng)
            ad.append(location)

            sales = Element("sales-agent")
            add_filed(sales, 'name', get_full_name(estate.employee))
            add_filed(sales, 'phone', "+" + str(estate.employee.phone))
            add_filed(sales, 'category', 'agency')
            add_filed(sales, 'photo', "{}{}.jpeg".format(PIC_BASE, estate.employee.pic))
            ad.append(sales)

            price = Element("price")
            add_filed(price, 'value', estate.price)
            add_filed(price, 'currency', 'RUB')
            ad.append(price)

            if not estate.type_enum == GROUND:
                area = Element("area")
                add_filed(area, 'value', estate.square)
                add_filed(area, 'init', 'кв. м')
                ad.append(area)

            if estate.type_enum == HOUSE or estate.type_enum == GROUND:
                lot_area = Element("lot-area")
                add_filed(lot_area, 'value', estate.square_ground)
                add_filed(lot_area, 'init', 'сотка')
                ad.append(lot_area)

            if estate.type_enum == RESIDENTIAL or estate.type_enum == HOUSE:
                renovation = estate.supple.get("renovation", "1")
                add_filed(ad, 'Renovation', RENOVATION_YANDEX.get(renovation))

            add_filed(ad, 'description', estate.comment)

            add_filed(ad, 'rooms', ROOMS_YANDEX.get(estate.rooms))

            if estate.type_enum == RESIDENTIAL:
                add_filed(ad, 'floor', estate.floor)
                add_filed(ad, 'built-year', '2022')
                has_closed_area = estate.location.supple.get("has_closed_area")
                add_filed(ad, 'guarded-building', has_closed_area)
                lift = estate.location.supple.get("has_lift")
                add_filed(ad, 'lift', lift)

            if not estate.type_enum == GROUND:
                add_filed(ad, 'floors-total', estate.location.floors)

            for media_image in estate.media.all():
                add_filed(ad, 'image', "{}{}.jpeg".format(PRESENTATION_BASE, media_image.link))
            root.append(ad)

        return XmlResponse(tostring(root, encoding="UTF-8", xml_declaration=True))


class CianApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        root = Element("feed")
        add_filed(root, 'feed_version', 2)
        edges = await query_estate({"has_cian": True})

        for estate in edges:
            ad = Element("object")
            add_filed(ad, 'ExternalId', estate.id)
            add_filed(ad, 'Description', estate.comment)
            add_filed(ad, 'Address', estate.location.address)

            coordinates = Element("Coordinates")
            add_filed(coordinates, 'Lat', estate.location.lat)
            add_filed(coordinates, 'Lng', estate.location.lng)
            ad.append(coordinates)

            phones = Element("Phones")
            phone_schema = Element("PhoneSchema")
            add_filed(phone_schema, 'CountryCode', "+7")
            add_filed(phone_schema, 'Number', str(estate.employee.phone)[1:])
            phones.append(phone_schema)
            ad.append(phones)

            photos = Element("Photos")
            for media_image in estate.media.all():
                photo_schema = Element("PhotoSchema")
                add_filed(photo_schema, 'FullUrl', "{}{}.jpeg".format(PRESENTATION_BASE, media_image.link))
                add_filed(photo_schema, 'IsDefault', False)
                photos.append(photo_schema)
            ad.append(photos)

            add_filed(ad, 'Category', CATEGORY_CIAN.get(estate.type_enum))

            if estate.type_enum == RESIDENTIAL:
                add_filed(ad, 'FlatRoomsCount', ROOMS_CIAN.get(estate.rooms))
                add_filed(ad, 'FloorNumber', estate.floor)

            if not estate.type_enum == GROUND:
                add_filed(ad, 'TotalArea', estate.square)

                building = Element("Building")
                add_filed(building, 'FloorsCount', estate.location.floors)
                ad.append(building)

            if estate.type_enum == HOUSE or estate.type_enum == GROUND:
                lot_area = Element("Land")
                add_filed(lot_area, 'Area', estate.square_ground)
                add_filed(lot_area, 'AreaUnitType', 'sotka')
                ad.append(lot_area)

            bargain_terms = Element("BargainTerms")
            add_filed(bargain_terms, 'Price', estate.price)
            add_filed(bargain_terms, 'SaleType', 'free')
            ad.append(bargain_terms)

            root.append(ad)

        return XmlResponse(tostring(root, encoding="UTF-8", xml_declaration=True))



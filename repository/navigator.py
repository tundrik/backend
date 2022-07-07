from asgiref.sync import sync_to_async
from django.db.models import Prefetch

from base.bsv import Bsv
from base.exceptions import NoData
from base.pagination import CursorPaginator

from base.helpers import (
    readable_price, encode_node_name, seconds_to_text, numeric_declension,
    phone_number_to_string, get_full_name
)
from constants import IMAGE_BASE, PIC_BASE, PRESENTATION_BASE, DEV
from domain.models import RESIDENTIAL, HOUSE, GROUND, COMMERCIAL, Estate, Project, Demand, Employee, EstateKitMember, \
    EstateMedia, ProjectMedia


class NavigatorRepository(Bsv):
    readable_role = {
        "boss": 'Директор',
        "mini_boss": 'Руководитель',
        "realtor": 'Отдел',
    }
    demand_image = {
        RESIDENTIAL: 'https://storage.yandexcloud.net/graph/static/crm/1.png',
        HOUSE: 'https://storage.yandexcloud.net/graph/static/crm/3.png',
        GROUND: 'https://storage.yandexcloud.net/graph/static/crm/4.png',
        COMMERCIAL: 'https://storage.yandexcloud.net/graph/static/crm/5.png',
    }
    readable_demand_caption = {
        RESIDENTIAL: 'квартиры',
        HOUSE: 'дома',
        GROUND: 'участка',
        COMMERCIAL: 'коммерции',
    }
    READABLE_ROOMS = {
        11: 'Квартира студия',
        12: 'Свободная планировка',
        1: '1-комнатная квартира',
        2: '2-комнатная квартира',
        3: '3-комнатная квартира',
        4: '4-комнатная квартира',
        5: '5-комнатная квартира',
        6: '6-комнатная квартира',
        7: 'Многокомнатная квартира',
        8: 'Многокомнатная квартира',
        9: 'Многокомнатная квартира',
        10: 'Многокомнатная квартира',
    }
    OBJECTS = {
        8: "Поселений (ИЖС)",
        9: "Сельхозназначения (СНТ, ДНП)",
        10: "Промназначения",
        11: "Гостиница",
        12: "Офисное помещение",
        13: "Помещение общественного питания",
        14: "Помещение свободного назначения",
        15: "Производственное помещение",
        16: "Складское помещение",
        17: "Торговое помещение",
        18: "Автосервис",
        19: "Здание",
    }

    async def retrieve_collection(self, *, node_type, params, path, query):
        """Вернуть коллекцию (project|estate|demand|employee) по фильтру с погинацией"""
        query_handler = getattr(self, 'query_' + node_type)
        entities, cursor = await query_handler(params, path, query)
        if not entities and not query.get("cursor"):
            raise NoData()

        edges, edges_ids = {}, []
        serialize_handler = getattr(self, 'serialize_' + node_type)
        for entity in entities:
            code_node = encode_node_name(entity.id, node_type)
            edges_ids.append(code_node)
            entity_dict = serialize_handler(entity, code_node)
            edges[code_node] = entity_dict

        return {
            'pageInfo': {
                'cursor': cursor,
                'ids': edges_ids,
                'node_type': node_type
            },
            'edges': edges,
        }

    async def retrieve_kit_members(self, *, pk):
        """Вернуть коллекцию участников подборки (estate)"""
        entities = await self.get_kit_members(pk)
        if not entities:
            raise NoData()
        edges, edges_ids = {}, []
        for entity in entities:
            estate = entity.estate
            code_node = encode_node_name(estate.id, "estate")
            edges_ids.append(code_node)
            entity_dict = self.serialize_estate(estate, code_node)
            edges[code_node] = entity_dict

        return {
            'pageInfo': {
                'cursor': None,
                'ids': edges_ids,
                'node_type': "estate"
            },
            'edges': edges,
        }

    def inspect_access(self, employee):
        if self.viewer.role == "boss":
            return True
        if self.viewer.role == "mini_boss" and employee.manager_id == self.viewer.pk:
            return True
        return self.viewer.pk == employee.pk

    def serialize_project(self, entity, code_node):
        present = {
            'price': "от " + readable_price(entity.price),
            'priceSquare': "{}{}".format(readable_price(entity.price_square), "/м²"),
            'square': "от {} {}".format(entity.square, "м²"),
        }
        return {
            "node": code_node,
            "node_type": "project",
            "has_edit": self.inspect_access(entity.employee),
            "person": self.serialize_person(entity.employee, "Риэлтор"),
            "mediaImages": self.serialize_media_images(entity.media.all()),
            "present": present,
            "comment": entity.comment,
            "caption": entity.project_name,
            "address": self.define_address(entity.location),
            "published": seconds_to_text(entity.published),
            "pk": "ID: " + str(entity.pk)
        }

    def serialize_estate(self, entity, code_node):
        if entity.type_enum == GROUND:
            square = numeric_declension(entity.square_ground, ['сотка', 'сотки', 'соток'])
            price_square = "{}{}".format(readable_price(entity.price_square_ground), "/сотка")
        else:
            square = "{} {}".format(entity.square, "м²")
            price_square = "{}{}".format(readable_price(entity.price_square), "/м²")

        present = {
            'price': readable_price(entity.price),
            'priceSquare': price_square,
            'square': square,
        }
        published = seconds_to_text(entity.published)
        if entity.has_avito:
            published = published + " • Avito"
        if entity.has_yandex:
            published = published + " • Yandex"
        if entity.has_cian:
            published = published + " • Cian"
        if entity.has_domclick:
            published = published + " • DomClick"

        if self.viewer.pk == entity.employee.pk:
            person = self.serialize_person(entity.customer, "Собственник")
        else:
            person = self.serialize_person(entity.employee, "Риэлтор")

        return {
            "node": code_node,
            "node_type": "estate",
            "has_edit": self.inspect_access(entity.employee),
            "person": person,
            "present": present,
            "mediaImages": self.serialize_media_images(entity.media.all()),
            "caption": self.define_caption(entity),
            "comment": entity.comment,
            "address": self.define_address(entity.location),
            "suple": entity.location.supple,
            "published": published,
            "pk": "ID: " + str(entity.pk)
        }

    def serialize_demand(self, entity, code_node):
        if entity.type_enum == GROUND:
            square = numeric_declension(entity.square_ground, ['сотка', 'сотки', 'соток'])
            price_square = "{}{}".format(readable_price(entity.price_square_ground), "/сотка")
        else:
            square = "{} {}".format(entity.square, "м²")
            price_square = "{}{}".format(readable_price(entity.price_square), "/м²")

        present = {
            'price': readable_price(entity.price),
            'priceSquare': price_square,
            'square': square,
        }

        if self.viewer.pk == entity.employee.pk:
            person = self.serialize_person(entity.customer, "Клиент")
        else:
            person = self.serialize_person(entity.employee, "Риэлтор")

        if entity.deal == "rent":
            deal = "Аренда"
        else:
            deal = "Покупка"
        caption = "{} {}".format(deal, self.readable_demand_caption.get(entity.type_enum)),
        return {
            "node": code_node,
            "node_type": "demand",
            "has_edit": self.inspect_access(entity.employee),
            "mediaImages": self.demand_image.get(entity.type_enum),
            "present": present,
            "person": person,
            "caption": caption,
            "comment": entity.comment,
            "published": seconds_to_text(entity.published),
            "pk": "ID: " + str(entity.pk)
        }

    def serialize_employee(self, entity, code_node):
        sub = self.readable_role.get(entity.role)
        if entity.manager:
            sub = sub + ": " + get_full_name(entity.manager)
        if not entity.has_active:
            sub = sub + " • Заблокирован"
        return {
            "node": code_node,
            "node_type": "employee",
            "has_edit": self.viewer.role == "boss",
            'person': self.serialize_person(entity, "Риэлтор"),
            'sub': phone_number_to_string(entity.phone)
        }

    @staticmethod
    def serialize_person(person, role):
        return {
            'pic': "{}{}.jpeg".format(PIC_BASE, person.pic),
            'name': get_full_name(person),
            'role': role,
            'phone': phone_number_to_string(person.phone),
        }

    @staticmethod
    def define_address(location):
        address = ""
        if location.district:
            address = location.district
        elif location.locality:
            address = location.locality

        if location.street:
            address = address + ", " + location.street

        if location.house:
            address = address + ", " + location.house
        return address

    @classmethod
    def define_caption(cls, estate):
        if estate.type_enum == RESIDENTIAL:
            readable_floors = "{}/{} этаж".format(estate.floor, estate.location.floors)
            if estate.object_type == 3:
                rooms = "Апартаменты"
            else:
                rooms = cls.READABLE_ROOMS.get(estate.rooms)
            return "{}, {}".format(rooms, readable_floors)

        elif estate.type_enum == HOUSE:
            return "{}-{} {}".format(
                estate.location.floors,
                "этажный дом, c участком ",
                numeric_declension(estate.square_ground, ['сотка', 'сотки', 'соток'])
            )

        elif estate.type_enum == GROUND:
            return "{} {}".format(
                "Участок ",
                cls.OBJECTS.get(estate.object_type),
            )

        elif estate.type_enum == COMMERCIAL:
            return cls.OBJECTS.get(estate.object_type)

    @staticmethod
    def serialize_media_images(media_images):
        media_images_result = []
        for media_image in media_images:
            media_image = {
                'linkPart': "{}{}.jpeg".format(IMAGE_BASE, media_image.link),
                'presentation': "{}{}.jpeg".format(PRESENTATION_BASE, media_image.link),
                'ranging': media_image.ranging,
            }
            media_images_result.append(media_image)

        return media_images_result

    @sync_to_async
    def query_project(self, params, path, query):
        gs_media = Prefetch('media', queryset=ProjectMedia.objects.order_by('ranging'))
        qs = Project.objects.filter(**params) \
            .prefetch_related(gs_media) \
            .prefetch_related('location') \
            .prefetch_related('employee')
        paginator = CursorPaginator(qs, path=path, query=query)
        entities_orm, cursor = paginator.get_instances()
        return entities_orm, cursor

    @sync_to_async
    def query_estate(self, params, path, query):
        gs_media = Prefetch('media', queryset=EstateMedia.objects.order_by('ranging'))
        qs = Estate.objects.filter(**params) \
            .prefetch_related(gs_media) \
            .prefetch_related('location') \
            .prefetch_related('customer') \
            .prefetch_related('employee')
        paginator = CursorPaginator(qs, path=path, query=query)
        entities_orm, cursor = paginator.get_instances()
        return entities_orm, cursor

    @sync_to_async
    def query_demand(self, params, path, query):
        qs = Demand.objects.filter(**params) \
            .prefetch_related('customer') \
            .prefetch_related('employee')
        paginator = CursorPaginator(qs, path=path, query=query)
        entities_orm, cursor = paginator.get_instances()
        return entities_orm, cursor

    @sync_to_async
    def query_employee(self, params, path, query):
        qs = Employee.objects.filter(**params).exclude(phone=79881607082)\
            .prefetch_related('manager')
        paginator = CursorPaginator(qs, path=path, query=query)
        entities_orm, cursor = paginator.get_instances()
        return entities_orm, cursor

    @sync_to_async
    def get_kit_members(self, pk):
        gs_media = Prefetch('estate__media', queryset=EstateMedia.objects.order_by('ranging'))
        gs = EstateKitMember.objects.filter(kit_id=pk)\
            .prefetch_related(gs_media) \
            .prefetch_related('estate__location') \
            .prefetch_related('estate__customer') \
            .prefetch_related('estate__employee')

        return list(gs)

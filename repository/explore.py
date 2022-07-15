from asgiref.sync import sync_to_async
from django.db.models import Prefetch

from base.bsv import Bsv
from base.exceptions import NoData
from base.pagination import CursorPaginator

from base.helpers import (
    readable_price, encode_node_name, seconds_to_text, numeric_declension,
    phone_number_to_string, get_full_name, decode_node_name
)
from constants import IMAGE_BASE, PIC_BASE, PRESENTATION_BASE, VIDEO_BASE
from domain.models import RESIDENTIAL, HOUSE, GROUND, COMMERCIAL, Estate, Project, EstateMedia, ProjectMedia, \
    EstateKitMember
from storage.store import Store


class ExploreRepository(Bsv):
    DETALE_ROOMS = {
        11: 'Студия',
        12: 'Свободноя планировка',
        1: '1',
        2: '2',
        3: '3',
        4: '4',
        5: '5',
        6: '6',
        7: '7',
        8: '8',
        9: '9',
        10: '10 и более',
    }
    READABLE_ROOMS = {
        11: 'Квартира студия',
        12: 'Квартира свободной планировки',
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

    async def retrieve_kit_members(self, *, pk):
        """Вернуть коллекцию участников подборки (estate)"""
        entities = await self.get_kit_members(pk)
        if not entities:
            raise NoData()
        edges, edges_ids = {}, []
        for entity in entities:
            estate = entity.estate
            kit = entity.kit
            code_node = encode_node_name(estate.id, "estate")
            edges_ids.append(code_node)
            entity_dict = self.serialize_kit(estate, code_node, kit)
            edges[code_node] = entity_dict

        return {
            'pageInfo': {
                'cursor': None,
                'ids': edges_ids,
                'node_type': "estate"
            },
            'edges': edges,
        }

    def serialize_kit(self, entity, code_node, kit):
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
        person = self.serialize_person(kit.employee, "Риэлтор")

        return {
            "node": code_node,
            "node_type": "estate",
            "person": person,
            "present": present,
            "mediaImages": self.serialize_media(entity.media.all()),
            "caption": self.define_caption(entity),
            "comment": entity.comment,
            "address": self.define_address(entity.location),
            "suple": entity.location.supple,
            "published": published,
            "pk": "ID: " + str(entity.pk),
            "lat": entity.location.lat,
            "lng": entity.location.lng,
            'savedByViewer': False,
            'has_kit': True,
        }

    async def retrive_node(self, *, code_node):
        pk, type_node = decode_node_name(code_node)
        handler = getattr(self, 'retrieve_' + type_node)
        return await handler(pk)

    async def retrieve_favorites(self, node_type):
        ids, ids_score = await Store.get_saved_score(self.viewer.guid, node_type)
        query_handler = getattr(self, 'query_favorites_' + node_type)
        entities = await query_handler(ids)
        if not entities:
            raise NoData()

        edges, edges_ids = {}, []
        set_saved = await Store.get_saved(self.viewer.guid, node_type)
        serialize_handler = getattr(self, 'serialize_' + node_type)
        for entity in entities:
            code_node = encode_node_name(entity.id, node_type)
            edges_ids.append(code_node)
            entity_dict = serialize_handler(entity, code_node, set_saved)
            edges[code_node] = entity_dict
        return {
            'pageInfo': {
                'cursor': None,
                'ids': edges_ids,
                'node_type': node_type
            },
            'edges': edges,
        }

    async def retrieve_estate(self, pk):
        entity = await self.query_estate_node(pk)
        code_node = encode_node_name(entity.id, "estate")
        set_saved = await Store.get_saved(self.viewer.guid, "estate")
        entity_dict = self.serialize_node_estate(entity, code_node, set_saved)
        return entity_dict

    async def retrieve_project(self, pk):
        entity = await self.query_project_node(pk)
        code_node = encode_node_name(entity.id, "project")
        set_saved = await Store.get_saved(self.viewer.guid, "project")
        entity_dict = self.serialize_node_project(entity, code_node, set_saved)
        return entity_dict

    async def retrieve_collection(self, *, node_type, params, path, query):
        """Вернуть коллекцию (project|estate) по фильтру с погинацией"""
        query_handler = getattr(self, 'query_' + node_type)
        entities, cursor = await query_handler(params, path, query)
        if not entities and not query.get("cursor"):
            raise NoData()

        edges, edges_ids = {}, []
        set_saved = await Store.get_saved(self.viewer.guid, node_type)
        serialize_handler = getattr(self, 'serialize_' + node_type)
        for entity in entities:
            code_node = encode_node_name(entity.id, node_type)
            edges_ids.append(code_node)
            entity_dict = serialize_handler(entity, code_node, set_saved)
            edges[code_node] = entity_dict

        return {
            'pageInfo': {
                'cursor': cursor,
                'ids': edges_ids,
                'node_type': node_type
            },
            'edges': edges,
        }

    def serialize_project(self, entity, code_node, set_saved):
        present = {
            'price': "от " + readable_price(entity.price),
            'priceSquare': "{}{}".format(readable_price(entity.price_square), "/м²"),
            'square': "от {} {}".format(entity.square, "м²"),
        }
        return {
            "node": code_node,
            "node_type": "project",
            "person": self.serialize_person(entity.employee, "Риэлтор"),
            "mediaImages": self.serialize_media(entity.media.all()),
            "present": present,
            "comment": entity.comment,
            "caption": entity.project_name,
            "address": self.define_address(entity.location),
            "published": seconds_to_text(entity.published),
            "pk": "ID: " + str(entity.pk),
            "lat": entity.location.lat,
            "lng": entity.location.lng,
            'savedByViewer': bool(str(entity.id) in set_saved),
            'has_kit': False,
        }

    def serialize_estate(self, entity, code_node, set_saved):
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
        person = self.serialize_person(entity.employee, "Риэлтор")

        return {
            "node": code_node,
            "node_type": "estate",
            "person": person,
            "present": present,
            "mediaImages": self.serialize_media(entity.media.all()),
            "caption": self.define_caption(entity),
            "comment": entity.comment,
            "address": self.define_address(entity.location),
            "suple": entity.location.supple,
            "published": published,
            "pk": "ID: " + str(entity.pk),
            "lat": entity.location.lat,
            "lng": entity.location.lng,
            'savedByViewer': bool(str(entity.id) in set_saved),
            'has_kit': False,
        }

    def serialize_node_project(self, entity, code_node, set_saved):
        items = [{
            "label": "Общая площадь:",
            "value": "от {} {}".format(entity.square, "м²"),
        }]

        return {
            "node": code_node,
            "node_type": "project",
            'price': "от " + readable_price(entity.price),
            'priceSquare': "{}{}".format(readable_price(entity.price_square), "/м²"),
            'items': items,
            "person": self.serialize_person(entity.employee, "Риэлтор"),
            "mediaImages": self.serialize_media(entity.media.all()),

            "comment": entity.comment,
            "caption": entity.project_name,
            "address": self.define_address(entity.location),
            "published": seconds_to_text(entity.published),
            "pk": "ID: " + str(entity.pk),
            "lat": entity.location.lat,
            "lng": entity.location.lng,
            'savedByViewer': bool(str(entity.id) in set_saved),
            'has_kit': False,
        }

    def serialize_node_estate(self, entity, code_node, set_saved):
        if entity.type_enum == GROUND:
            square = numeric_declension(entity.square_ground, ['сотка', 'сотки', 'соток'])
            price_square = "{}{}".format(readable_price(entity.price_square_ground), "/сотка")
        else:
            square = "{} {}".format(entity.square, "м²")
            price_square = "{}{}".format(readable_price(entity.price_square), "/м²")

        published = seconds_to_text(entity.published)
        person = self.serialize_person(entity.employee, "Риэлтор")

        return {
            "node": code_node,
            "node_type": "estate",
            "person": person,
            'price': readable_price(entity.price),
            'priceSquare': price_square,
            'items': self.define_items(entity, square),
            "mediaImages": self.serialize_media(entity.media.all()),
            "caption": self.define_caption(entity),
            "comment": entity.comment,
            "address": self.define_address(entity.location),
            "suple": entity.location.supple,
            "published": published,
            "pk": "ID: " + str(entity.pk),
            "lat": entity.location.lat,
            "lng": entity.location.lng,
            'savedByViewer': bool(str(entity.id) in set_saved),
            'has_kit': False,
        }

    @classmethod
    def define_items(cls, estate, square):
        items = [{
            "label": "Общая площадь:",
            "value": square,
        }]

        if estate.type_enum == RESIDENTIAL:
            items.extend([
                {
                    "label": "Количество комнат:",
                    "value": cls.DETALE_ROOMS.get(estate.rooms),
                }, {
                    "label": "Этаж:",
                    "value": "{} из {}".format(estate.floor, estate.location.floors),
                }
            ])

        if estate.type_enum == HOUSE:
            items.extend([
                {
                    "label": "Площадь участка:",
                    "value": numeric_declension(estate.square_ground, ['сотка', 'сотки', 'соток']),
                }, {
                    "label": "Этажность:",
                    "value": estate.location.floors,
                }
            ])

        return items

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
            return "{} {} {}".format(
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
    def serialize_media(medias):
        media_result = []
        for media in medias:
            if media.type_enum == "image":
                media_item = {
                    'type_enum': media.type_enum,
                    'linkPart': "{}{}.jpeg".format(IMAGE_BASE, media.link),
                    'presentation': "{}{}.jpeg".format(PRESENTATION_BASE, media.link),
                    'ranging': media.ranging,
                }
            else:
                media_item = {
                    'type_enum': media.type_enum,
                    'linkPart': "{}{}.mp4".format(VIDEO_BASE, media.link),
                    'ranging': media.ranging,
                }
            media_result.append(media_item)

        return media_result

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
        qs = Estate.objects.filter(has_archive=False, has_site=True, **params) \
            .prefetch_related(gs_media) \
            .prefetch_related('location') \
            .prefetch_related('employee')
        paginator = CursorPaginator(qs, path=path, query=query)
        entities_orm, cursor = paginator.get_instances()
        return entities_orm, cursor

    @sync_to_async
    def query_estate_node(self, pk):
        gs_media = Prefetch('media', queryset=EstateMedia.objects.order_by('ranging'))
        return Estate.objects.filter(has_archive=False, has_site=True, pk=pk) \
            .prefetch_related(gs_media) \
            .prefetch_related('location') \
            .prefetch_related('employee').first()

    @sync_to_async
    def query_project_node(self, pk):
        gs_media = Prefetch('media', queryset=ProjectMedia.objects.order_by('ranging'))
        return Project.objects.filter(pk=pk) \
            .prefetch_related(gs_media) \
            .prefetch_related('location') \
            .prefetch_related('employee').first()

    @sync_to_async
    def query_favorites_estate(self, ids):
        gs_media = Prefetch('media', queryset=EstateMedia.objects.order_by('ranging'))
        qs = Estate.objects.filter(id__in=ids) \
            .prefetch_related(gs_media) \
            .prefetch_related('location') \
            .prefetch_related('employee')
        return list(qs)

    @sync_to_async
    def query_favorites_project(self, ids):
        gs_media = Prefetch('media', queryset=ProjectMedia.objects.order_by('ranging'))
        qs = Project.objects.filter(id__in=ids) \
            .prefetch_related(gs_media) \
            .prefetch_related('location') \
            .prefetch_related('employee')
        return list(qs)

    @sync_to_async
    def get_kit_members(self, pk):
        gs_media = Prefetch('estate__media', queryset=EstateMedia.objects.order_by('ranging'))
        gs = EstateKitMember.objects.filter(kit_id=pk) \
            .prefetch_related('kit__employee') \
            .prefetch_related(gs_media) \
            .prefetch_related('estate__location')
        return list(gs)

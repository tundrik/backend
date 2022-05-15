from asgiref.sync import sync_to_async

from base.bsv import Bsv
from base.helpers import decode_node_name, phone_number_to_string, get_full_name
from domain.models import Demand, Employee, Project, Estate, GROUND, HOUSE, RESIDENTIAL, COMMERCIAL

ROLE = [
    {"value": "realtor", "label": "Риэлтор"},
    {"value": "mini_boss", "label": "Руководитель"},
    {"value": "boss", "label": "Директор"},
]

RENOVATION = [
    {"value": "1", "label": "Требуется"},
    {"value": "2", "label": "Косметический"},
    {"value": "3", "label": "Евро"},
    {"value": "4", "label": "Дизайнерский"},
]
STATUS = [
    {"value": "izhs", "label": "ИЖС"},
    {"value": "snt", "label": "СНТ"},
]

DEAL = [
    {"value": "bay", "label": "Покупка"},
    {"value": "rent", "label": "Аренда"},
]

ROOMS = [
    {"value": "1", 'label': "1"},
    {"value": "2", 'label': "2"},
    {'value': "3", 'label': "3"},
    {'value': "4", 'label': "4"},
    {"value": "5", 'label': "5"},
    {'value': "6", 'label': "6"},
    {'value': "7", 'label': "7"},
    {'value': "8", 'label': "8"},
    {'value': "9", 'label': "9"},
    {'value': "10", 'label': "10"},
    {"value": "12", "label": "Свободная планировка"},
    {"value": "11", "label": "Студия"},
]


RESIDENTIAL_OBJECTS = [
    {"value": 1, "label": "Жилое помещение"},
    {"value": 2, "label": "Квартира"},
    {"value": 3, "label": "Апартамент"},
]

HOUSE_OBJECTS = [
    {"value": 4, "label": "Дом"},
    {"value": 5, "label": "Дача"},
    {"value": 6, "label": "Коттедж"},
    {"value": 7, "label": "Таунхаус"},
]

GROUND_OBJECTS = [
    {"value": 8, "label": "Поселений (ИЖС)"},
    {"value": 9, "label": "Сельхозназначения (СНТ, ДНП)"},
    {"value": 10, "label": "Промназначения"},
]

COMMERCIAL_OBJECTS = [
    {"value": 11, "label": "Гостиница"},
    {"value": 12, "label": "Офисное помещение"},
    {"value": 13, "label": "Помещение общественного питания"},
    {"value": 14, "label": "Помещение свободного назначения"},
    {"value": 15, "label": "Производственное помещение"},
    {"value": 16, "label": "Складское помещение"},
    {"value": 17, "label": "Торговое помещение"},
    {"value": 18, "label": "Автосервис"},
    {"value": 19, "label": "Здание"},
]

PROJECT_TYPE_ENUM = [
    {"value": "ЖК", "label": "Жилой комплекс"},
    {"value": "КП", "label": "Коттеджный поселок"},
]

ESTATE_TYPE_ENUM = [
    {"value": "residential", "label": "Квартира"},
    {"value": "house", "label": "Дом"},
    {"value": "ground", "label": "Участок"},
    {"value": "commercial", "label": "Коммерция"},
]

DEMAND_TYPE_ENUM = [
    {"value": "residential", "label": "Квартиры"},
    {"value": "house", "label": "Дома"},
    {"value": "ground", "label": "Участка"},
    {"value": "commercial", "label": "Коммерции"},
]


class FormRepository(Bsv):
    async def retrive_node(self, *, code_node):
        pk, type_node = decode_node_name(code_node)
        handler = getattr(self, 'retrieve_' + type_node)
        return await handler(pk)

    async def retrieve_project(self, pk):
        """Вернуть комплекс"""
        entity = await self.query_project(pk)
        return {
            "type_node": "project",
            "type_enum": entity.type_enum,
            "form": [
                self.get_input("Данные комплекса", entity.price, "Минимальная цена", "number", "price"),
                self.get_input(None, entity.price_square, "Минимальная цена за м²", "number", "price_square"),
                self.get_input(None, entity.square, "Минимальная площадь", "number", "square"),
                self.get_input("Описание", entity.comment, "Описание", "textarea", "comment"),
            ],
        }

    async def retrieve_estate(self, pk):
        """Вернуть объект"""
        entity = await self.query_estate(pk)
        type_enum = entity.type_enum
        form = [
            self.get_input("Данные собственника", entity.customer.first_name, "Имя", "text", "first_name"),
            self.get_input(None, phone_number_to_string(entity.customer.phone), "Телефон", "text", "phone"),
        ]

        if type_enum == RESIDENTIAL:
            form.extend([
                self.get_select("Данные объекта", entity.object_type, "Тип объекта", "object_type",
                                RESIDENTIAL_OBJECTS),
            ])

        if type_enum == HOUSE:
            form.extend([
                self.get_select("Данные объекта", entity.object_type, "Тип объекта", "object_type", HOUSE_OBJECTS),
            ])

        if type_enum == GROUND:
            form.extend([
                self.get_select("Данные объекта", entity.object_type, "Тип объекта", "object_type", GROUND_OBJECTS),
            ])

        if type_enum == COMMERCIAL:
            form.extend([
                self.get_select("Данные объекта", entity.object_type, "Тип объекта", "object_type", COMMERCIAL_OBJECTS),
            ])

        form.extend([
            self.get_input("", entity.price, "Цена", "number", "price"),
        ])

        if not type_enum == GROUND:
            form.extend([
                self.get_input(None, entity.square, "Площадь", "number", "square"),
                self.get_select(None, entity.rooms, "Количество комнат", "rooms", ROOMS),
                self.get_select(None, entity.supple.get("renovation"), "Ремонт", "renovation", RENOVATION),
            ])

        if type_enum == GROUND or type_enum == HOUSE:
            form.extend([
                self.get_input(None, entity.square_ground, "Площадь участка", "number", "square_ground"),
            ])
        if type_enum == HOUSE:
            form.extend([
                self.get_select(None, entity.supple.get("status"), "Статус участка", "status", STATUS),
            ])
        settings = [
            self.get_input("Выгрузка", entity.has_site, "Показывать на сайте", "checkbox", "has_site"),
            self.get_input(None, entity.has_avito, "Avito", "checkbox", "has_avito"),
            self.get_input(None, entity.has_yandex, "Yandex", "checkbox", "has_yandex"),
            self.get_input(None, entity.has_cian, "Cian", "checkbox", "has_cian"),
            self.get_input(None, entity.has_domclick, "DomClick", "checkbox", "has_domclick"),
        ]
        return {
            "type_node": "estate",
            "extra": {
                "type_enum": type_enum,
            },
            "form": [
                *form,
                *settings,
                self.get_input("Описание объекта", entity.comment, "", "textarea", "comment"),
            ],
        }

    async def retrieve_employee(self, pk):
        """Вернуть сотрудника"""
        entity = await self.query_employee(pk)
        manager_options = await self.query_manager()
        extra = {}
        form = [
            self.get_select("Данные сотрудника", entity.role, "Роль сотрудника", "role", ROLE),
        ]

        if entity.role == "realtor":
            form.extend([
                self.get_select(None, entity.manager_id, "Отдел", "manager", manager_options),
            ])

        form.extend([
            self.get_input(None, entity.first_name, "Имя", "text", "first_name"),
            self.get_input(None, entity.last_name, "Фамилия", "text", "last_name"),
            self.get_input(None, phone_number_to_string(entity.phone), "Телефон", "text", "phone"),
        ])
        if entity.role == "mini_boss" or entity.role == "realtor":
            form.extend([
                self.get_input("Настройки", entity.has_active, "Доступ в CRM", "checkbox", "has_active"),
            ])
        return {
            "type_node": "employee",
            "extra": extra,
            "form": form
        }

    async def retrieve_demand(self, pk):
        """Вернуть заявку"""
        entity = await self.query_demand(pk)
        type_enum = entity.type_enum
        form = [
            self.get_input("Данные клиента", entity.customer.first_name, "Имя", "text", "first_name"),
            self.get_input(None, phone_number_to_string(entity.customer.phone), "Телефон", "text", "phone"),
            self.get_select("Данные заявки", entity.deal, "Тип сделки", "deal", DEAL),
            self.get_input(None, entity.price, "Бюджет", "number", "price"),
        ]
        if not type_enum == GROUND:
            form.extend([
                self.get_input(None, entity.square, "Желаемая площадь", "number", "square"),
            ])
        if type_enum == GROUND or type_enum == HOUSE:
            form.extend([
                self.get_input(None, entity.square_ground, "Желаемая площадь участка", "number", "square_ground"),
            ])
        return {
            "type_node": "demand",
            "extra": {
                "type_enum": type_enum,
            },
            "form": [
                *form,
                self.get_input("Детали заявки", entity.comment, "", "textarea", "comment"),
            ],
        }

    @sync_to_async
    def query_project(self, pk):
        return Project.objects.get(pk=pk)

    @sync_to_async
    def query_estate(self, pk):
        return Estate.objects.filter(pk=pk).select_related('customer').first()

    @sync_to_async
    def query_employee(self, pk):
        return Employee.objects.filter(pk=pk).first()

    @sync_to_async
    def query_demand(self, pk):
        return Demand.objects.filter(pk=pk).select_related('customer').first()

    @sync_to_async
    def query_manager(self):
        qs = Employee.objects.filter(role="mini_boss")
        edges = []
        for entity in list(qs):
            edges.append({
                "label": get_full_name(entity),
                "value": entity.id
            })
        return edges

    @staticmethod
    def get_input(title, value, label, input_type, name):
        return {
            "title": title,
            "label": label,
            "type": input_type,
            "name": name,
            "value": value,
        }

    @staticmethod
    def get_select(title, value, label, name, options):
        return {
            "title": title,
            "label": label,
            "type": "select",
            "value": value,
            "name": name,
            "options": options
        }

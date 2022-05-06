from asgiref.sync import sync_to_async

from base.bsv import Bsv
from base.helpers import decode_node_name, phone_number_to_string
from domain.models import Demand, Employee, Project, Estate, GROUND, HOUSE, RESIDENTIAL, COMMERCIAL

ROLE = [
    {"value": "realtor", "label": "Риэлтор"},
    {"value": "mini_boss", "label": "Руководитель"},
]

RESIDENTIAL_OBJECTS = [
    {"value": 1, "label": "Квартира"},
    {"value": 2, "label": "Апартамент"},
    {"value": 3, "label": "Жилое помещение"},
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
    {"value": "residential", "label": "Заявка на квартиру"},
    {"value": "house", "label": "Заявка на дом"},
    {"value": "ground", "label": "Заявка на участок"},
    {"value": "commercial", "label": "Заявка на коммерцию"},
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
                self.get_select("Тип объекта", entity.object_type, "", "object_type", RESIDENTIAL_OBJECTS),
            ])

        if type_enum == HOUSE:
            form.extend([
                self.get_select("Тип объекта", entity.object_type, "", "object_type", HOUSE_OBJECTS),
            ])

        if type_enum == GROUND:
            form.extend([
                self.get_select("Тип объекта", entity.object_type, "", "object_type", GROUND_OBJECTS),
            ])

        if type_enum == COMMERCIAL:
            form.extend([
                self.get_select("Тип объекта", entity.object_type, "", "object_type", COMMERCIAL_OBJECTS),
            ])

        form.extend([
            self.get_input("Данные объекта", entity.price, "Цена", "number", "price"),
        ])

        if not type_enum == GROUND:
            form.extend([
                self.get_input(None, entity.square, "Площадь", "number", "square"),
            ])
        if type_enum == GROUND or type_enum == HOUSE:
            form.extend([
                self.get_input(None, entity.square_ground, "Площадь участка", "number", "square_ground"),
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
            "type_enum": type_enum,
            "form": [
                *form,
                *settings,
                self.get_input("Описание объекта", entity.comment, "", "textarea", "comment"),
            ],
        }

    async def retrieve_employee(self, pk):
        """Вернуть сотрудника"""
        entity = await self.query_employee(pk)
        return {
            "type_node": "employee",
            "form": [
                self.get_input("Данные сотрудника", entity.first_name, "Имя", "text", "first_name"),
                self.get_input(None, entity.last_name, "Фамилия", "text", "last_name"),
                self.get_input(None, phone_number_to_string(entity.phone), "Телефон", "text", "phone"),
                self.get_select("Роль сотрудника", entity.role, "", "role", ROLE),
            ],
        }

    async def retrieve_demand(self, pk):
        """Вернуть заявку"""
        entity = await self.query_demand(pk)
        type_enum = entity.type_enum
        form = [
            self.get_input("Данные клиента", entity.customer.first_name, "Имя", "text", "first_name"),
            self.get_input(None, phone_number_to_string(entity.customer.phone), "Телефон", "text", "phone"),
            self.get_input("Данные заявки", entity.price, "Бюджет", "number", "price"),
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
            "type_enum": type_enum,
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
        return Employee.objects.get(pk=pk)

    @sync_to_async
    def query_demand(self, pk):
        return Demand.objects.filter(pk=pk).select_related('customer').first()

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

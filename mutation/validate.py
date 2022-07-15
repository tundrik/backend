import httpx
import orjson
from base.exceptions import ValidateError
from domain.models import GROUND, HOUSE, RESIDENTIAL, COMMERCIAL


def len_inspect(val, le, mes):
    if len(val) < le:
        raise ValidateError(mes)
    return val


def int_inspect(val, le, mes):
    if not val:
        raise ValidateError(mes)
    val = int(''.join(filter(str.isdigit, val)))
    if val < le:
        raise ValidateError(mes)
    return val


def validate_phone(phone):
    if not phone:
        raise ValidateError("Введите номер телефона")
    phone_number = int(''.join(filter(str.isdigit, phone)))

    if not len(str(phone_number)) == 11:
        raise ValidateError(f"Некорректный номер <br/>{phone}")

    return phone_number


def validate_employee(payload):
    print(payload)
    first_name = len_inspect(payload.get("first_name"), 3, "Введите имя")
    last_name = len_inspect(payload.get("last_name"), 3, "Введите фамилию")
    phone = validate_phone(payload.get("phone"))
    valid = {
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "search_full": "{} {} {}".format(first_name, last_name, phone),
        "manager_id": payload.get("manager"),
        "has_active": bool(payload.get('has_active')),
    }
    role = payload.get('role')
    if role:
        valid["role"] = role
    return valid


def validate_customer(payload):
    first_name = len_inspect(payload.get("first_name"), 3, "Введите имя")
    phone = validate_phone(payload.get("phone"))
    valid = {
        "first_name": first_name,
        "search_full": "{} {}".format(first_name, phone),
        "phone": phone
    }
    return valid


def validate_demand(payload):
    type_enum = payload.get("type_enum")
    deal = payload.get("deal"),
    if deal == "bay":
        price = int_inspect(payload.get("price"), 1000000, "Введите бюджет<br>от 1 000 000")
    else:
        price = int_inspect(payload.get("price"), 10000, "Введите бюджет<br>от 10 000")

    valid = {
        "type_enum": type_enum,
        "deal": payload.get("deal"),
        "price": price,
        "comment": payload.get("comment"),
    }

    if not type_enum == GROUND:
        square = int_inspect(payload.get("square"), 10, "Введите желаемую площадь")
        price_square = int(int(price) / int(square))
        valid['square'] = square
        valid['price_square'] = price_square

    if type_enum == GROUND or type_enum == HOUSE:
        square_ground = int_inspect(payload.get("square_ground"), 3, "Введите желаемую площадь участка")
        price_square_ground = int(int(price) / int(square_ground))
        valid['square_ground'] = square_ground
        valid['price_square_ground'] = price_square_ground

    return valid


def validate_location_mutate(payload):
    type_enum = payload.get("type_enum")
    valid = {}
    supple = {}

    if not type_enum == GROUND:
        valid["floors"] = payload.get('floors')

    if type_enum == GROUND or type_enum == HOUSE:
        supple["has_electricity"] = bool(payload.get('has_electricity'))
        supple["has_water"] = bool(payload.get('has_water'))
        supple["has_gas"] = bool(payload.get('has_gas'))
        supple["has_sewerage"] = bool(payload.get('has_sewerage'))

    if type_enum == RESIDENTIAL or type_enum == COMMERCIAL:
        supple["has_lift"] = bool(payload.get('has_lift'))
        supple["has_rubbish_chute"] = bool(payload.get('has_rubbish_chute'))
        supple["has_closed_area"] = bool(payload.get('has_closed_area'))

    valid["supple"] = supple

    return valid


async def validate_location(payload):
    address = payload.get("address")
    base_url = "https://geocode-maps.yandex.ru/1.x"
    apikey = "8e802446-42a3-4c58-9137-da5007e86ae7"
    params = {
        "geocode": "город Сочи " + address,
        "apikey": apikey,
        "format": "json",
        "results": 1
    }

    valid = {
        "address": address,
    }

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.get(base_url, params=params)
        parsed = orjson.loads(response.text)

    feature_members = parsed["response"]["GeoObjectCollection"]["featureMember"]

    if not feature_members:
        raise ValidateError("Некорректный адрес")

    if feature_members:
        print(feature_members)
        geo_object = feature_members[0]["GeoObject"]
        full_address = geo_object["metaDataProperty"]["GeocoderMetaData"]["text"]
        valid["address"] = full_address
        point = geo_object["Point"]["pos"].split()
        valid["lat"] = point[1]
        valid["lng"] = point[0]
        components = geo_object["metaDataProperty"]["GeocoderMetaData"]["Address"]["Components"]
        for component in components:
            print(component)
            if component.get("kind") == "street":
                valid["street"] = component.get("name")

            if component.get("kind") == "house":
                valid["house"] = component.get("name")

            if component.get("kind") == "district":
                valid["district"] = component.get("name")

            if component.get("kind") == "locality":
                valid["locality"] = component.get("name")

    type_enum = payload.get("type_enum")

    supple = {}

    if not type_enum == GROUND:
        valid["floors"] = payload.get('floors')

    if type_enum == GROUND or type_enum == HOUSE:
        supple["has_electricity"] = bool(payload.get('has_electricity'))
        supple["has_water"] = bool(payload.get('has_water'))
        supple["has_gas"] = bool(payload.get('has_gas'))
        supple["has_sewerage"] = bool(payload.get('has_sewerage'))

    if type_enum == RESIDENTIAL or type_enum == COMMERCIAL:
        supple["has_lift"] = bool(payload.get('has_lift'))
        supple["has_rubbish_chute"] = bool(payload.get('has_rubbish_chute'))
        supple["has_closed_area"] = bool(payload.get('has_closed_area'))

    valid["supple"] = supple

    return valid


def validate_estate(payload):
    type_enum = payload.get("type_enum")

    price = int_inspect(payload.get("price"), 1000000, "Введите цену")
    comment_len = len(payload.get("comment"))
    comment = len_inspect(
        payload.get("comment"), 50,
        f"Описание - требуется еще {50 - comment_len} символов"
    ),
    supple = {}
    valid = {
        "type_enum": type_enum,
        "price": price,
        "comment": payload.get("comment"),
        "object_type": payload.get('object_type'),
        "has_site": bool(payload.get('has_site')),
        "has_avito": bool(payload.get('has_avito')),
        "has_yandex": bool(payload.get('has_yandex')),
        "has_cian": bool(payload.get('has_cian')),
        "has_domclick": bool(payload.get('has_domclick')),
    }

    if not type_enum == GROUND:
        square = int_inspect(payload.get("square"), 10, "Введите площадь")
        price_square = int(int(price) / int(square))
        valid['square'] = square
        valid['price_square'] = price_square
        valid["rooms"] = payload.get('rooms')
        supple["renovation"] = payload.get('renovation')

    if type_enum == GROUND or type_enum == HOUSE:
        square_ground = int_inspect(payload.get("square_ground"), 4, "Введите площадь участка")
        price_square_ground = int(int(price) / int(square_ground))
        valid['square_ground'] = square_ground
        valid['price_square_ground'] = price_square_ground

    if type_enum == HOUSE:
        supple["status"] = payload.get('status')
        supple["walls_type"] = payload.get('walls_type')

    if type_enum == RESIDENTIAL or type_enum == COMMERCIAL:
        floors = int_inspect(payload.get("floors"), 1, "Введите этажность")
        floor = int_inspect(payload.get("floor"), 1, "Введите этаж")
        if floor > floors:
            raise ValidateError("Этаж не может быть больше этажности")
        valid["floor"] = floor
        supple["has_last_floor"] = bool(floor == floors)

    if payload.get('project'):
        valid["project_id"] = payload.get('project')

    valid["supple"] = supple

    return valid


def validate_project(payload):
    type_enum = payload.get("type_enum")

    price = int_inspect(payload.get("price"), 1000000, "Введите минимальную цену")
    square = int_inspect(payload.get("square"), 10, "Введите минимальную площадь")
    price_square = int_inspect(payload.get("price_square"), 10000, "Введите минимальную цену за м²")

    valid = {
        "type_enum": type_enum,
        "price": price,
        "square": square,
        "price_square": price_square,
        "comment": payload.get('comment'),
    }

    project_name = payload.get("project_name")

    if project_name is not None and len(project_name) < 3:
        raise ValidateError("Введите название")

    if project_name:
        valid["project_name"] = project_name

    return valid

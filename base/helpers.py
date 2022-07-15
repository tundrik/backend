import secrets
import time
import uuid
from base64 import urlsafe_b64encode, urlsafe_b64decode

from math import floor


def get_full_name(person):
    if person.first_name or person.last_name:
        full_name = person.first_name + " " + person.last_name
    else:
        full_name = "аноним"
    return full_name.strip()


def generate_pin() -> str:
    """Генерация 4 значного пин кода"""
    secrets_number = secrets.choice(range(1000, 10000))
    return format(secrets_number, '04')


def generate_uuid() -> uuid:
    """Генерация uuid4"""
    guid = uuid.uuid4()
    return guid


def encode_node_name(pk, type_):
    """Кодирование node name"""
    string_global = "{}:{}".format(pk, type_)
    encoded = urlsafe_b64encode(string_global.encode('utf8')).decode('ascii')
    return encoded.rstrip("=")


def decode_node_name(node):
    """Декодирование node name"""
    padding = 4 - (len(node) % 4)
    string_global = node + ("=" * padding)
    decoded = urlsafe_b64decode(string_global.encode('ascii')).decode('utf8')
    return decoded.split(':')


def str_to_bool(string: str) -> bool:
    """Используется в ответах от Redis"""
    if string == 'True':
        return True
    elif string == 'False':
        return False
    else:
        raise ValueError


def to_camel_case(snake_str: str) -> str:
    """Конвертация ключей в camelCase"""
    components = snake_str.lstrip('__').split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def to_pascal_case_type(snake_str: str) -> str:
    """Конвертация ключей в PascalCase + Type"""
    components = snake_str.lstrip('__').split('_')
    return ''.join(x.title() for x in components) + "Type"


def readable_price(num: int) -> str:
    magnitude_dict = {
        0: '',
        1: 'тыс',
        2: 'млн',
        3: 'млр',
        4: 'тлн',
    }
    magnitude = 0
    while num >= 1000:
        magnitude += 1
        num = num / 1000
    orig = float(round(num, 1))
    if orig.is_integer() or magnitude == 1:
        orig = int(orig)
    return f'{orig} {magnitude_dict[magnitude]}'


def numeric_declension(number: int, forms: list) -> str:
    """
    Оригинал на PHP:
        https://codinghamster.info/php/correct-plural-form-of-a-noun/
    использование:
        numeric_declension(11, ['день', 'дня', 'дней'])
    """
    rest = number % 10
    str_number = str(number)
    number = int(str_number[-2:])

    if rest == 1 and number != 11:
        return "{} {}".format(number, forms[0])
    elif rest in [2, 3, 4] and number not in [12, 13, 14]:
        return "{} {}".format(number, forms[1])
    else:
        return "{} {}".format(number, forms[2])


def phone_number_to_string(number: int) -> str:
    string = str(number)
    return "{}{} {} {} {} {}".format("+", string[:1], string[1:4], string[4:7], string[7:9],  string[9:11])


def seconds_to_text(unix: int) -> str:
    """
    Преобразует количество секунду в текст (сколько прошло времени)
    :param unix: Количество секунд от 1970
    :return: сколько прошло времени
    """
    secs = int(time.time()) - unix
    result = 1
    result_text = ['день', 'дня', 'дней']
    if secs <= 43200:
        return "сегодня"
    elif secs >= 31536000:

        result = secs // 31536000
        result_text = ['год', 'года', 'лет']
    elif secs >= 2592000:
        result = secs // 2592000
        result_text = ['месяц', 'месяца', 'месяцев']
    elif secs >= 86400:
        result = secs // 86400
        result_text = ['день', 'дня', 'дней']
    return f"{numeric_declension(result, result_text)} назад"

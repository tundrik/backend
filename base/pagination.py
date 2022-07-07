from base64 import urlsafe_b64encode, urlsafe_b64decode
from urllib.parse import urlencode
from django.db.models import Field, Func
from django.db.models import Value, TextField

from abc import ABC
from base.exceptions import InvalidCursor
from constants import HOST_BACKEND


class TupleField(Field):
    pass


class Tuple(Func, ABC):
    output_field = TupleField()
    function = ''

    def get_group_by_cols(self, alias=None):
        cols = []
        for expr in self.source_expressions:
            cols += expr.get_group_by_cols()
        return cols


class CursorPaginator:
    """
    TODO: Переписать sort ordering
    """
    _delimiter = '|'

    def __init__(
            self,
            queryset,
            path,
            query,
            first: int = None,
    ):
        self.queryset = queryset
        self.path = path
        self.query = query
        self.first = first or 10
        sort = query.get('sort')
        self._ordering = ['-ranging', '-pk']

        if sort is not None:
            self._ordering[0] = sort
            if sort.startswith('-'):
                self._ordering[1] = '-pk'
            else:
                self._ordering[1] = 'pk'

        print(sort)

        self.ordering = self._ordering

    def get_instances(self):
        queryset = self.queryset.order_by(*self.ordering)
        after = self.query.get('cursor')
        query = self.query.copy()

        if after is not None:
            queryset = self._apply_cursor(after, queryset)

        queryset = queryset[:self.first + 1]

        queryset = list(queryset)

        items = queryset[:self.first]

        has_additional = len(queryset) > len(items)

        if has_additional:
            query.update({'cursor': self.get_cursor(items[-1])})
            cursor = HOST_BACKEND + self.path + '?' + urlencode(query)
        else:
            cursor = None
        return items, cursor

    def _apply_cursor(self, cursor, queryset):
        position = self._decode_cursor(cursor)

        is_reversed = self.ordering[0].startswith('-')
        queryset = queryset.annotate(_cursor=Tuple(*[o.lstrip('-') for o in self.ordering]))
        current_position = [Value(p, output_field=TextField()) for p in position]
        if is_reversed:
            return queryset.filter(_cursor__lt=Tuple(*current_position))
        return queryset.filter(_cursor__gt=Tuple(*current_position))

    def _decode_cursor(self, cursor):
        try:
            padding = 4 - (len(cursor) % 4)
            string = cursor + ("=" * padding)
            orderings = urlsafe_b64decode(string.encode('ascii')).decode('utf8')
            return orderings.split(self._delimiter)
        except (TypeError, ValueError):
            raise InvalidCursor()

    def _encode_cursor(self, position):
        encoded = urlsafe_b64encode(self._delimiter.join(position).encode('utf8')).decode('ascii')
        return encoded.rstrip("=")

    def _position_from_instance(self, instance):
        position = []
        for order in self.ordering:
            parts = order.lstrip('-').split('__')
            attr = instance
            while parts:
                attr = getattr(attr, parts[0])
                parts.pop(0)
            position.append(str(attr))

        return position

    def get_cursor(self, instance):
        return self._encode_cursor(self._position_from_instance(instance))

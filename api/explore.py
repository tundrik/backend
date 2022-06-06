import asyncio

from django.core.handlers.asgi import ASGIRequest

from base.endpoint import Endpoint
from base.exceptions import NoData
from base.helpers import decode_node_name
from base.response import OrjsonResponse, no_data
from repository.explore import ExploreRepository

REGEX_EXPLORE = '(?:(?P<node_type>(project|estate))/)' \
                  '(?:(?P<type_enum>(residential|house|ground|commercial))/)?' \
                  '(?:price-min-(?P<price_min>\\d+)/)?' \
                  '(?:price-max-(?P<price_max>\\d+)/)?' \
                  '(?:square-min-(?P<square_min>\\d+)/)?' \
                  '(?:square-max-(?P<square_max>\\d+)/)?' \
                  '(?:square-ground-min-(?P<square_ground_min>\\d+)/)?' \
                  '(?:square-ground-max-(?P<square_ground_max>\\d+)/)?' \
                  '(?:sort-(?P<sort>\\D+)/)?$'


class ExploreApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        """Получить коллекцию (project|estate)"""
        repository = ExploreRepository(viewer=self.viewer)
        node_type = kwargs.get('node_type')
        query = request.GET.copy()
        query["sort"] = kwargs.get("sort")
        search = query.get("search")
        params = self.generate_filter(node_type, kwargs, search)
        try:
            response_data = await repository.retrieve_collection(
                node_type=node_type, params=params, path=request.path, query=query
            )
            return OrjsonResponse(response_data)
        except NoData:
            return no_data(request)

    def generate_filter(self, node_type, kwargs, search):
        print(self)
        type_enum = kwargs.get("type_enum")
        price_min = kwargs.get("price_min")
        price_max = kwargs.get("price_max")
        square_min = kwargs.get("square_min")
        square_max = kwargs.get("square_max")
        square_ground_min = kwargs.get("square_ground_min")
        square_ground_max = kwargs.get("square_ground_max")

        params = {}

        if search:
            if search.isdigit():
                params['pk'] = search
                return params
            if node_type == "estate":
                params['location__address__trigram_word_similar'] = search
            if node_type == "project":
                params['project_name__trigram_word_similar'] = search

        if type_enum:
            params['type_enum'] = type_enum

        if price_min:
            params['price__gte'] = price_min

        if price_max:
            params['price__lte'] = price_max

        if square_min:
            params['square__gte'] = square_min

        if square_max:
            params['square__lte'] = square_max

        if square_ground_min:
            params['square_ground__gte'] = square_ground_min

        if square_ground_max:
            params['square_ground__lte'] = square_ground_max

        return params


class FavoriteApi(Endpoint):
    async def get(self, request: ASGIRequest, node_type=None):
        """Получить коллекцию сохраненных"""
        repository = ExploreRepository(viewer=self.viewer)
        try:
            response_data = await repository.retrieve_favorites(node_type)
            return OrjsonResponse(response_data)
        except NoData:
            return no_data(request)


class NodeApi(Endpoint):
    async def get(self, request: ASGIRequest, code_node=None):
        """Вернуть (estate|project)"""
        repository = ExploreRepository(viewer=self.viewer)
        response_data = await repository.retrive_node(code_node=code_node)
        return OrjsonResponse(response_data)


class SiteKitApi(Endpoint):
    async def get(self, request: ASGIRequest, code_node=None):
        """Получить коллекцию подборку"""
        pk, type_node = decode_node_name(code_node)
        repository = ExploreRepository(viewer=self.viewer)
        try:
            response_data = await repository.retrieve_kit_members(pk=pk)
            return OrjsonResponse(response_data)
        except NoData:
            return no_data(request)

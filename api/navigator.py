from django.core.handlers.asgi import ASGIRequest

from base.endpoint import Endpoint
from base.exceptions import NoData
from base.response import OrjsonResponse, no_data
from repository.navigator import NavigatorRepository


REGEX_NAVIGATOR = '(?:(?P<node_type>(project|estate|demand|employee))/)' \
                  '(?:(?P<type_enum>(residential|house|ground|commercial))/)?' \
                  '(?:(?P<deal>(bay|rent))/)?' \
                  '(?:has-main-(?P<has_main>on)/)?' \
                  '(?:has-site-(?P<has_site>on)/)?' \
                  '(?:has-avito-(?P<has_avito>on)/)?' \
                  '(?:has-yandex-(?P<has_yandex>on)/)?' \
                  '(?:has-cian-(?P<has_cian>on)/)?' \
                  '(?:has-domclick-(?P<has_domclick>on)/)?' \
                  '(?:has-archive-(?P<has_archive>on)/)?' \
                  '(?:price-min-(?P<price_min>\\d+)/)?' \
                  '(?:price-max-(?P<price_max>\\d+)/)?' \
                  '(?:square-min-(?P<square_min>\\d+)/)?' \
                  '(?:square-max-(?P<square_max>\\d+)/)?' \
                  '(?:square-ground-min-(?P<square_ground_min>\\d+)/)?' \
                  '(?:square-ground-max-(?P<square_ground_max>\\d+)/)?' \
                  '(?:sort-(?P<sort>\\D+)/)?$'


class NavigatorApi(Endpoint):
    async def get(self, request: ASGIRequest, **kwargs):
        """Получить коллекцию (project|estate|demand|employee)"""
        repository = NavigatorRepository(viewer=self.viewer)
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
        type_enum = kwargs.get("type_enum")
        deal = kwargs.get("deal")
        price_min = kwargs.get("price_min")
        price_max = kwargs.get("price_max")
        square_min = kwargs.get("square_min")
        square_max = kwargs.get("square_max")
        square_ground_min = kwargs.get("square_ground_min")
        square_ground_max = kwargs.get("square_ground_max")

        params = {}

        if node_type == "estate" or node_type == "demand":
            params['has_archive'] = False

        if search:
            if search.isdigit():
                params['pk'] = search
                return params
            if node_type == "estate":
                params['location__address__trigram_word_similar'] = search
            if node_type == "demand":
                params['comment__trigram_word_similar'] = search
            if node_type == "project":
                params['project_name__trigram_word_similar'] = search

        if type_enum:
            params['type_enum'] = type_enum

        if deal:
            params['deal'] = deal

        if kwargs.get("has_main"):
            params['employee_id'] = self.viewer.pk

        if kwargs.get("has_site"):
            params['has_site'] = True

        if kwargs.get("has_avito"):
            params['has_avito'] = True

        if kwargs.get("has_yandex"):
            params['has_yandex'] = True

        if kwargs.get("has_cian"):
            params['has_cian'] = True

        if kwargs.get("has_domclick"):
            params['has_domclick'] = True

        if kwargs.get("has_archive"):
            params['has_archive'] = True

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

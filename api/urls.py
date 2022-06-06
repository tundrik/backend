from django.urls import path, include, re_path

from api.explore import REGEX_EXPLORE, ExploreApi, NodeApi, FavoriteApi, SiteKitApi
from api.features import FeaturesApi, ToggleFeatureApi
from api.feed import AvitoApi, YandexApi, CianApi
from api.login import LoginApi
from api.mutate import AddApi, UpdateApi, DeleteApi, UploadApi, MediaApi
from api.search import SuggestionsApi, ProjectApi, TestApi, ManagerApi, MirabaseApi
from api.profile import ViewerApi, KitApi, KitMembersApi, SavedApi, DeleteSavedApi
from api.navigator import REGEX_NAVIGATOR, NavigatorApi
from base.response import no_data, forbidden, bad_request

handler404 = no_data
handler403 = forbidden
handler400 = bad_request

profile_url = [
    path('viewer/', ViewerApi.dispatch),
    path('saved/', SavedApi.dispatch),
    path('saved/delete/<str:code_node>/', DeleteSavedApi.dispatch),
    path('kit/', KitApi.dispatch),
    path('kit/<str:code_node>/', KitMembersApi.dispatch),
]

internal_url = [
    re_path('navigator/' + REGEX_NAVIGATOR, NavigatorApi.dispatch),
    path('add/<str:type_node>/', AddApi.dispatch),
    path('upload/<str:type_node>/', UploadApi.dispatch),
    path('media/<str:type_node>/', MediaApi.dispatch),
    path('mutate/<str:code_node>/', UpdateApi.dispatch),
    path('delete/<str:code_node>/', DeleteApi.dispatch),
    path('search/suggestions/', SuggestionsApi.dispatch),
    path('search/project/', ProjectApi.dispatch),
    path('search/manager/', ManagerApi.dispatch),
    path('profile/', include(profile_url)),
]

feed_url = [
    path('avito/', AvitoApi.dispatch),
    path('yandex/', YandexApi.dispatch),
    path('cian/', CianApi.dispatch),
]

site_url = [
    re_path('explore/' + REGEX_EXPLORE, ExploreApi.dispatch),
    path('favorite/<str:node_type>/', FavoriteApi.dispatch),
    path('node/<str:code_node>/', NodeApi.dispatch),
    path('kit/<str:code_node>/', SiteKitApi.dispatch),
    path('features/', FeaturesApi.dispatch),
    path('features/favorite/<str:code_node>/', ToggleFeatureApi.dispatch),
]


urlpatterns = [
    path('site/', include(site_url)),
    path('crm/', include(internal_url), {'access_level': 'internal'}),
    path('login/', LoginApi.dispatch),
    path('feed/', include(feed_url)),
    path('test/', TestApi.dispatch),
    path('mirabase/', MirabaseApi.dispatch),
]

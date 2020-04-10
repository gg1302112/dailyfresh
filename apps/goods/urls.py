from django.conf.urls import url
from .views import Goods, DetailView, ListView


urlpatterns = [
    url(r'^index$', Goods.as_view(), name='index'),
    url(r'^detail/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$', ListView.as_view(), name='list'),
]

from django.conf.urls import url, include
from .views import Goods, DetailView, ListView


urlpatterns = [
    url(r'^index$', Goods.as_view(), name='index'),
    url(r'^detail/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$', ListView.as_view(), name='list'),
    url(r'^search/$', include('haystack.urls'), name='search'),  # 全文检索框架
]

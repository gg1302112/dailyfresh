from django.conf.urls import url
from .views import OrderPlaceView, OrderCommitView
from . import views

urlpatterns = [
    url(r'^place$', OrderPlaceView.as_view(), name="place"),
    url(r'^commit$', OrderCommitView.as_view(), name="commit"),
]

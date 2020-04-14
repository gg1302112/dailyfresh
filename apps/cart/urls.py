from django.conf.urls import url
from .views import AddView

urlpatterns = [
    url(r'^add$', AddView.as_view(), name='add'),
]

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .views import Register, ActiveView, LoginView, UserinfoView, UserorderView, AddressView, LogoutView

urlpatterns = [
    # url(r'^register$', views.register, name='register'),
    url(r'^register$', Register.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(R'^logout$', LogoutView.as_view(), name='logout'),

    # url(r'^$', login_required(UserinfoView.as_view()), name='user'),
    # url(r'^order$', login_required(UserorderView.as_view()), name='order'),
    # url(r'^address$', login_required(AddressView.as_view()), name='address'),

    url(r'^$', UserinfoView.as_view(), name='user'),
    url(r'^order$', UserorderView.as_view(), name='order'),
    url(r'^address$', AddressView.as_view(), name='address'),


]

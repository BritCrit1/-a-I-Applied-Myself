from django.urls import path
from . import views

urlpatterns = [
    path("", views.paywall, name="subscription"),
    path("config/", views.configuration),
    path("verify/", views.verify),
    path("subscribe-native/", views.paywall),
    path("restore-native/", views.paywall),
]

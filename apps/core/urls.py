from django.urls import path

from apps.core import views


urlpatterns = [
    path("signup/", views.signup, name="signup"),
]

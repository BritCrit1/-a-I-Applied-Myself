from django.urls import path

from apps.profiles import views


urlpatterns = [
    path("resume/", views.upload_resume, name="resume_upload"),
    path("candidate/", views.confirm_candidate_profile, name="profile_confirm"),
    path("search/", views.search_preferences, name="search_preferences"),
]

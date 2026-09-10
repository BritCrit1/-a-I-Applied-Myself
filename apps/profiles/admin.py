from django.contrib import admin

from apps.profiles.models import CandidateProfile, Resume, SearchPreference


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("original_filename", "user__username", "user__email")


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "email", "location", "confirmed_at")
    search_fields = ("full_name", "email", "user__username")


@admin.register(SearchPreference)
class SearchPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "search_intent", "zip_code", "search_radius_miles", "work_mode", "priority")
    list_filter = ("search_intent", "work_mode", "priority")

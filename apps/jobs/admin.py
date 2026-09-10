from django.contrib import admin

from apps.jobs.models import (
    AgentTask,
    Application,
    ApplicationAttempt,
    Communication,
    FollowUp,
    Job,
    JobSource,
    RunSetting,
)


@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "provider_key", "is_active")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "work_mode", "match_score", "source")
    list_filter = ("work_mode", "career_alignment", "source")
    search_fields = ("title", "company", "location", "source_url")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "state", "auto_submit_authorized", "last_state_change_at")
    list_filter = ("state", "auto_submit_authorized")
    search_fields = ("user__username", "job__title", "job__company")


admin.site.register(ApplicationAttempt)
admin.site.register(AgentTask)
admin.site.register(Communication)
admin.site.register(FollowUp)
admin.site.register(RunSetting)

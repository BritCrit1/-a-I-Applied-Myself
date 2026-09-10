from django.contrib import admin

from apps.core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "actor_type", "action", "target_type", "target_id", "user")
    list_filter = ("actor_type", "action", "target_type")
    search_fields = ("action", "target_type", "target_id", "user__username", "user__email")


from django.contrib import admin

from .models import InviteCode


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "is_used", "created_at")
    list_filter = ("is_used", "created_at")
    search_fields = ("code",)
    readonly_fields = ("created_at",)

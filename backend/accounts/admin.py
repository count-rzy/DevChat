
from django.contrib import admin

from .models import InviteCode, UserProfile


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "is_used", "created_at")
    list_filter = ("is_used", "created_at")
    search_fields = ("code",)
    readonly_fields = ("created_at",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "preferred_language")
    search_fields = ("user__username", "display_name")

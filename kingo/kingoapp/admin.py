from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserCustom, BingoBoard, Player, GameSession

class CustomUserAdmin(UserAdmin):
    model = UserCustom
    list_display = ("username", "first_name", "telegram_user_id", "telegram_username", "last_name", "phone", "joined_at", "balance", "wins", "losses", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Bingo Stats", {"fields": ("phone", "balance", "wins", "losses")}),
    )
    search_fields = ("username", "first_name", "last_name", "phone", "telegram_username")  # Add telegram_username to search

admin.site.register(UserCustom, CustomUserAdmin)
admin.site.register(BingoBoard)
admin.site.register(Player)
admin.site.register(GameSession)

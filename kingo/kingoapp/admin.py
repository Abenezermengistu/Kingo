from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserCustom, BingoBoard, Player, GameSession

class CustomUserAdmin(UserAdmin):
    model = UserCustom
    list_display = ("username", "first_name", "last_name", "phone", "joined_at", "balance", "wins", "losses", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Bingo Stats", {"fields": ("phone", "balance", "wins", "losses")}),
    )

admin.site.register(UserCustom, CustomUserAdmin)
admin.site.register(BingoBoard)
admin.site.register(Player)
admin.site.register(GameSession)

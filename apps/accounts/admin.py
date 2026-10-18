from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class JecUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("JEC", {"fields": ("role", "federation", "phone")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("JEC", {"fields": ("role", "federation", "phone")}),)
    list_display = ("username", "email", "role", "federation", "is_staff", "is_active")
    list_filter = UserAdmin.list_filter + ("role", "federation")

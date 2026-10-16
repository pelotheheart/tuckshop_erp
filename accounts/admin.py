from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Branch, User
# Register your models here.
@admin.register(User)
class TuckshopUserAdmin(UserAdmin):
    #Show the role in the list of users
    list_display = ["username", "role","branch", "is_active"]
    #and add a role box to Django's normal edit-user and add-user pages.
    fieldsets = UserAdmin.fieldsets + (("Tuckshop", {"fields": ["role" , "branch"]}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Tuckshop", {"fields": ["role", "branch"]}),)
admin.site.register(Branch)
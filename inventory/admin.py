from django.contrib import admin

from .models import Inventory, Product

admin.site.register(Product)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    # Show these columns in the admin site's list of stock rows.
    list_display = ["product", "branch", "quantity"]
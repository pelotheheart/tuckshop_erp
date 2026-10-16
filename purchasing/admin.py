from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["supplier_name", "contact_name", "phone", "email", "is_active"]


class PurchaseOrderItemInline(admin.TabularInline):
    # Show an order's items as a little table on the order's own page.
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "order_date", "supplier", "branch", "status"]
    inlines = [PurchaseOrderItemInline]
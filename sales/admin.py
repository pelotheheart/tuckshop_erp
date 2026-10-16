from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    # Show a sale's items as a little table on the sale's own page.
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ["id", "sale_date", "cashier", "branch", "total_amount"]
    inlines = [SaleItemInline]
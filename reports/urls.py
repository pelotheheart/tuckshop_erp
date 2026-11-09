
from django.urls import path

from . import views

urlpatterns = [
    path("", views.reports_home, name="reports_home"),

    path("sales/", views.sales_report, name="sales_report"),
    path("cashiers/", views.cashier_report, name="cashier_report"),
    path("inventory/", views.inventory_report, name="inventory_report"),
    path("purchasing/", views.purchasing_report, name="purchasing_report"),

    path("export/sales/", views.export_sales_csv, name="export_sales_csv"),
    path("export/cashiers/", views.export_cashier_csv, name="export_cashier_csv"),
    path("export/inventory/", views.export_inventory_csv, name="export_inventory_csv"),
    path("export/purchasing/", views.export_purchasing_csv, name="export_purchasing_csv"),
]

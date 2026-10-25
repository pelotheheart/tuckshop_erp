from django.urls import path

from . import views

urlpatterns = [
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/add/", views.supplier_add, name="supplier_add"),
    path("suppliers/<int:pk>/edit/", views.supplier_edit, name="supplier_edit"),
    path("suppliers/<int:pk>/toggle-active/", views.supplier_toggle_active, name="supplier_toggle_active"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/new/", views.order_create, name="order_create"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/fulfil/", views.order_fulfil, name="order_fulfil"),
    path("orders/<int:pk>/cancel/", views.order_cancel, name="order_cancel"),
]

from django.urls import path

from . import views

urlpatterns = [
    path("pos/", views.pos, name="pos"),
    path("pos/products/", views.product_lookup, name="pos_product_lookup"),
    path("pos/checkout/", views.checkout, name="pos_checkout"),
    path("history/", views.sale_list, name="sale_list"),
    path("<int:pk>/receipt/", views.sale_receipt, name="sale_receipt"),
]
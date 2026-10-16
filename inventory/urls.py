from django.urls import path 
from . import views

urlpatterns = [
    path("products/add/", views.product_add, name="product_add"),
    path("products/search/", views.product_search, name="product_search"),
]
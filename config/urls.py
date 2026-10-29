"""The URL table: which address runs which Python function.

Django checks these patterns from top to bottom and calls the function of
the first one that matches.
"""

from django.contrib import admin
from django.urls import include,path

from core import views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # name="..." lets templates link to a page with {% url 'home' %} instead of typing the address
    path("", views.home, name="home"),  # http://127.0.0.1:8000/
    path("inventory/", include("inventory.urls")),
    path("", include("accounts.urls")),
    path("reports/", include("reports.urls")),
]

from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from inventory.models import Inventory

@login_required
def home(request):
    now = datetime.now().strftime("%H:%M:%S")
    stock = (
        Inventory.objects.filter(branch=request.user.branch, product__is_active=True)
        .select_related("product")
        .order_by("product__product_name")
    )
    # render() fills in the template with these values and returns the finished HTML
    return render(request, "core/home.html", {"now": now, "stock": stock})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render

from accounts.models import ADMIN, OWNER
from accounts.permissions import role_required

from .forms import ProductForm
from .models import Inventory


@role_required(OWNER, ADMIN)
def product_add(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            # Adding a product writes to two tables: the product itself, and its stock row at
            # the user's branch. The transaction makes them all-or-nothing: if the second
            # write fails, MySQL undoes the first one too.
            with transaction.atomic():
                product = form.save()#save product first so ID is available for stock foreign key
                Inventory.objects.create(branch=request.user.branch, product=product, quantity=0)
            messages.success(request, f"{product.product_name} was added.")
            return redirect("home")
    else:
        form = ProductForm()
    return render(request, "inventory/product_form.html", {"form": form})


@login_required
def product_search(request):
    q = request.GET.get("q", "")
    # Search the stock at the user's own branch, so the results can show how many are left.
    rows = (
        Inventory.objects.filter(
            branch=request.user.branch,
            product__is_active=True,
            product__product_name__icontains=q,
        )
        .select_related("product")
        .order_by("product__product_name")
    )
    results = []
    for row in rows:
        results.append({
            "name": row.product.product_name,
            "barcode": row.product.barcode,
            # We send the price as text so it stays exactly "18.50".
            "price": str(row.product.selling_price),
            "stock": row.quantity,
            "low_stock": row.is_low_stock,
        })
    return JsonResponse({"results": results})
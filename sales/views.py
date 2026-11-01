import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from accounts.models import ADMIN, OWNER
from accounts.permissions import role_required
from inventory.models import Inventory

from .models import Sale
from .services import SaleRejected, process_sale


@login_required
def pos(request):
    return render(request, "sales/pos.html")


@login_required
def product_lookup(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"results": []})
    rows = (
        Inventory.objects.filter(branch=request.user.branch, product__is_active=True)
        .filter(Q(product__product_name__icontains=q) | Q(product__barcode=q))
        .select_related("product")
        .order_by("product__product_name")[:20]
    )
    results = []
    for row in rows:
        results.append({
            "id": row.product.id,
            "name": row.product.product_name,
            "price": str(row.product.selling_price),
            "stock": row.quantity,
        })
    return JsonResponse({"results": results})

@login_required
@require_POST
def checkout(request):
    try:
        data = json.loads(request.body)
        cart = {}
        for item in data["items"]:
            product_id = int(item["id"])
            quantity = int(item["qty"])
            if quantity < 1:
                raise ValueError
            cart[product_id] = cart.get(product_id, 0) + quantity
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "The cart couldn't be read. Refresh the page and try again."}, status=400)

    try:
        sale = process_sale(request.user, list(cart.items()))
    except SaleRejected as error:
        return JsonResponse({"error": str(error)}, status=409)
    return JsonResponse({"receipt_url": reverse("sale_receipt", args=[sale.id])})

@login_required
def sale_receipt(request, pk):
    sales = Sale.objects.select_related("branch", "cashier")
    # Owners and admins can open any receipt from their branch, but a cashier only their own.
    if request.user.has_role(OWNER, ADMIN):
        sales = sales.filter(branch=request.user.branch)
    else:
        sales = sales.filter(cashier=request.user)
    sale = get_object_or_404(sales, pk=pk)
    items = sale.items.select_related("product")
    return render(request, "sales/receipt.html", {"sale": sale, "items": items})


@role_required(OWNER, ADMIN)
def sale_list(request):
    day = parse_date(request.GET.get("date", "")) or timezone.now().date()
    day_sales = Sale.objects.filter(branch=request.user.branch, sale_date__date=day)
    day_total = day_sales.aggregate(total=Sum("total_amount"))["total"] or 0
    sales = (
        day_sales.select_related("cashier")
        .annotate(item_count=Sum("items__quantity"))
        .order_by("-sale_date")
    )
    return render(request, "sales/sale_list.html", {"sales": sales, "day": day, "day_total": day_total})
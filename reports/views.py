
import csv
from functools import wraps
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Sum, Count, Avg

from accounts.models import ADMIN, OWNER, CASHIER
from sales.models import Sale
from inventory.models import Inventory
from purchasing.models import PurchaseOrder
from django.contrib.auth import get_user_model

# Only logged-in Owners and Administrators can access reports.
def reports_access_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.has_role(OWNER, ADMIN):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


@reports_access_required
def reports_home(request):
    return render(request, "reports/reports_home.html")


@reports_access_required
def sales_report(request):
    today = timezone.now().date()
    period = request.GET.get("period", "7")
    start_date = None
    end_date = today

    # Set the date range selected by the user.
    if period == "today":
        start_date = today
    elif period == "7":
        start_date = today - timedelta(days=6)
    elif period == "30":
        start_date = today - timedelta(days=29)
    elif period == "365":
        start_date = today - timedelta(days=364)
    elif period == "custom":
        start_date = parse_date(request.GET.get("start_date", ""))
        end_date = parse_date(request.GET.get("end_date", ""))

        if not start_date or not end_date or start_date > end_date:
            start_date = today - timedelta(days=6)
            end_date = today
            period = "7"
    else:
        period = "7"
        start_date = today - timedelta(days=6)

    # Retrieve sales within the selected dates.
    sales = Sale.objects.select_related(
        "cashier", "branch"
    ).filter(
        sale_date__date__gte=start_date,
        sale_date__date__lte=end_date,
    )

    # Owners can see all branches. Administrators are limited to their branch.
    if not request.user.has_role(OWNER):
        sales = sales.filter(branch=request.user.branch)

    # List all active cashier accounts, including those with no sales.
    User = get_user_model()
    cashiers = User.objects.filter(
        role__role_name="Cashier",
        is_active=True,
    ).order_by("username")

    # Administrators only see cashiers assigned to their branch.
    if not request.user.has_role(OWNER):
        cashiers = cashiers.filter(branch=request.user.branch)

    # Filter sales by the selected cashier.
    cashier_id = request.GET.get("cashier", "")
    if cashier_id.isdigit():
        sales = sales.filter(cashier_id=int(cashier_id))

    # Calculate totals using the filtered sales.
    total_revenue = sales.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    return render(
        request,
        "reports/sales_report.html",
        {
            "sales": sales.order_by("-sale_date"),
            "cashiers": cashiers,
            "cashier_id": cashier_id,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": total_revenue,
            "total_transactions": sales.count(),
        },
    )



# The remaining report pages are placeholders until their calculations are added.

@reports_access_required
def cashier_report(request):
    # Administrators can only see cashiers from their own branch.
    sales = Sale.objects.all()

    if not request.user.has_role(OWNER):
        sales = sales.filter(branch=request.user.branch)

    # Group sales by cashier and calculate their performance.
    cashiers = (
        sales.values("cashier_id", "cashier__username")
        .annotate(
            total_transactions=Count("id"),
            total_revenue=Sum("total_amount"),
            average_ticket=Avg("total_amount"),
        )
        .order_by("cashier__username")
    )

    return render(
        request,
        "reports/cashier_report.html",
        {"cashiers": cashiers},
    )



@reports_access_required
def inventory_report(request):
    # Administrators can only view stock for their assigned branch.
    inventory = Inventory.objects.select_related(
        "product", "branch"
    )

    if not request.user.has_role(OWNER):
        inventory = inventory.filter(branch=request.user.branch)

    inventory_rows = list(inventory.order_by("product__product_name"))

    total_cost = 0
    total_retail = 0
    total_profit = 0

    for item in inventory_rows:
        item.cost_value = item.quantity * item.product.cost_price
        item.retail_value = item.quantity * item.product.selling_price
        item.gross_profit = item.retail_value - item.cost_value

        # Calculate the margin as a percentage of expected retail value.
        item.profit_margin = (
            item.gross_profit / item.retail_value * 100
            if item.retail_value else 0
        )

        total_cost += item.cost_value
        total_retail += item.retail_value
        total_profit += item.gross_profit

    total_margin = (
        total_profit / total_retail * 100
        if total_retail else 0
    )

    return render(
        request,
        "reports/inventory_report.html",
        {
            "inventory_rows": inventory_rows,
            "total_cost": total_cost,
            "total_retail": total_retail,
            "total_profit": total_profit,
            "total_margin": total_margin,
            "low_stock_count": sum(
                1 for item in inventory_rows if item.is_low_stock
            ),
        },
    )

@reports_access_required
def purchasing_report(request):
    # Administrators can only view orders for their assigned branch.
    orders = PurchaseOrder.objects.select_related(
        "supplier", "branch"
    ).prefetch_related("items")

    if not request.user.has_role(OWNER):
        orders = orders.filter(branch=request.user.branch)

    orders = list(orders.order_by("-order_date", "-id"))

    supplier_spend = {}
    pending_count = 0
    fulfilled_count = 0
    cancelled_count = 0
    total_fulfilled_spend = 0

    for order in orders:
        order.total_amount = sum(
            (item.quantity * item.cost_price for item in order.items.all()),
            start=0,
        )

        if order.status == PurchaseOrder.Status.PENDING:
            pending_count += 1
        elif order.status == PurchaseOrder.Status.FULFILLED:
            fulfilled_count += 1
            total_fulfilled_spend += order.total_amount

            supplier_id = order.supplier_id
            if supplier_id not in supplier_spend:
                supplier_spend[supplier_id] = {
                    "supplier_name": order.supplier.supplier_name,
                    "total_spend": 0,
                }
            supplier_spend[supplier_id]["total_spend"] += order.total_amount
        elif order.status == PurchaseOrder.Status.CANCELLED:
            cancelled_count += 1

    return render(
        request,
        "reports/purchasing_report.html",
        {
            "orders": orders,
            "supplier_spend": sorted(
                supplier_spend.values(),
                key=lambda supplier: supplier["total_spend"],
                reverse=True,
            ),
            "pending_count": pending_count,
            "fulfilled_count": fulfilled_count,
            "cancelled_count": cancelled_count,
            "total_fulfilled_spend": total_fulfilled_spend,
        },
    )


# These CSV export endpoints will be implemented after the reports are completed.

@reports_access_required
def export_sales_csv(request):
    today = timezone.now().date()
    period = request.GET.get("period", "7")
    start_date = None
    end_date = today

    if period == "today":
        start_date = today
    elif period == "7":
        start_date = today - timedelta(days=6)
    elif period == "30":
        start_date = today - timedelta(days=29)
    elif period == "365":
        start_date = today - timedelta(days=364)
    elif period == "custom":
        start_date = parse_date(request.GET.get("start_date", ""))
        end_date = parse_date(request.GET.get("end_date", ""))

        if not start_date or not end_date or start_date > end_date:
            start_date = today - timedelta(days=6)
            end_date = today
    else:
        start_date = today - timedelta(days=6)

    # Apply the same branch restrictions as the Sales Report page.
    sales = Sale.objects.select_related(
        "cashier", "branch"
    ).filter(
        sale_date__date__gte=start_date,
        sale_date__date__lte=end_date,
    )

    if not request.user.has_role(OWNER):
        sales = sales.filter(branch=request.user.branch)

    cashier_id = request.GET.get("cashier", "")
    if cashier_id.isdigit():
        sales = sales.filter(cashier_id=int(cashier_id))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Sale ID",
        "Date and Time",
        "Cashier",
        "Branch",
        "Total Amount (R)",
    ])

    for sale in sales.order_by("-sale_date"):
        writer.writerow([
            sale.id,
            sale.sale_date.strftime("%Y-%m-%d %H:%M:%S"),
            sale.cashier.username,
            sale.branch.branch_name,
            sale.total_amount,
        ])

    return response



@reports_access_required
def export_cashier_csv(request):
    # Administrators can only export results for their own branch.
    sales = Sale.objects.all()

    if not request.user.has_role(OWNER):
        sales = sales.filter(branch=request.user.branch)

    cashiers = (
        sales.values("cashier_id", "cashier__username")
        .annotate(
            total_transactions=Count("id"),
            total_revenue=Sum("total_amount"),
            average_ticket=Avg("total_amount"),
        )
        .order_by("cashier__username")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="cashier_performance.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        "Cashier",
        "Total Transactions",
        "Total Revenue (R)",
        "Average Transaction Value (R)",
    ])

    for cashier in cashiers:
        writer.writerow([
            cashier["cashier__username"],
            cashier["total_transactions"],
            cashier["total_revenue"] or 0,
            cashier["average_ticket"] or 0,
        ])

    return response



@reports_access_required
def export_inventory_csv(request):
    # Administrators can only export stock from their assigned branch.
    inventory = Inventory.objects.select_related(
        "product", "branch"
    )

    if not request.user.has_role(OWNER):
        inventory = inventory.filter(branch=request.user.branch)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="inventory_valuation.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        "Branch",
        "Product",
        "Quantity",
        "Cost Price (R)",
        "Selling Price (R)",
        "Cost Value (R)",
        "Expected Retail Value (R)",
        "Potential Gross Profit (R)",
        "Gross Profit Margin (%)",
        "Stock Status",
    ])

    for item in inventory.order_by("product__product_name"):
        cost_value = item.quantity * item.product.cost_price
        retail_value = item.quantity * item.product.selling_price
        gross_profit = retail_value - cost_value

        margin = (
            gross_profit / retail_value * 100
            if retail_value else 0
        )

        writer.writerow([
            item.branch.branch_name,
            item.product.product_name,
            item.quantity,
            item.product.cost_price,
            item.product.selling_price,
            cost_value,
            retail_value,
            gross_profit,
            round(margin, 2),
            "Low Stock" if item.is_low_stock else "In Stock",
        ])

    return response



@reports_access_required
def export_purchasing_csv(request):
    # Administrators can only export orders from their assigned branch.
    orders = PurchaseOrder.objects.select_related(
        "supplier", "branch"
    ).prefetch_related("items")

    if not request.user.has_role(OWNER):
        orders = orders.filter(branch=request.user.branch)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="purchasing_report.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        "Order ID",
        "Order Date",
        "Supplier",
        "Branch",
        "Status",
        "Total Amount (R)",
    ])

    for order in orders.order_by("-order_date", "-id"):
        total_amount = sum(
            (
                item.quantity * item.cost_price
                for item in order.items.all()
            ),
            start=0,
        )

        writer.writerow([
            order.id,
            order.order_date,
            order.supplier.supplier_name,
            order.branch.branch_name,
            order.status,
            total_amount,
        ])

    return response


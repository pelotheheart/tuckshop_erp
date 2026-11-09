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
from django.contrib.auth import get_user_model

from accounts.models import ADMIN, OWNER, Branch
from sales.models import Sale
from inventory.models import Inventory
from purchasing.models import PurchaseOrder


# Only logged-in Owners and Administrators can access reports.
def reports_access_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.has_role(OWNER, ADMIN):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


def parse_date_filters(request, default_period="7"):
    today = timezone.now().date()
    period = request.GET.get("period", default_period)

    if period == "all":
        start_date = None
        end_date = None
    elif period == "today":
        start_date = today
        end_date = today
    elif period == "7":
        start_date = today - timedelta(days=6)
        end_date = today
    elif period == "30":
        start_date = today - timedelta(days=29)
        end_date = today
    elif period == "365":
        start_date = today - timedelta(days=364)
        end_date = today
    elif period == "custom":
        start_date = parse_date(request.GET.get("start_date", ""))
        end_date = parse_date(request.GET.get("end_date", ""))

        if not start_date or not end_date or start_date > end_date:
            start_date = today - timedelta(days=6)
            end_date = today
            period = "7"
    else:
        period = default_period
        if default_period == "7":
            start_date = today - timedelta(days=6)
            end_date = today
        elif default_period == "all":
            start_date = None
            end_date = None
        else:
            start_date = today - timedelta(days=6)
            end_date = today

    return period, start_date, end_date


def get_branches_and_filter(request, queryset):
    branch_id_param = request.GET.get("branch", "")
    selected_branch_id = int(branch_id_param) if branch_id_param.isdigit() else ""

    if not request.user.has_role(OWNER):
        queryset = queryset.filter(branch=request.user.branch)
        branches = Branch.objects.filter(id=request.user.branch.id)
        selected_branch_id = request.user.branch.id
    else:
        branches = Branch.objects.all().order_by("branch_name")
        if selected_branch_id:
            queryset = queryset.filter(branch_id=selected_branch_id)
    return queryset, branches, selected_branch_id


@reports_access_required
def reports_home(request):
    return render(request, "reports/reports_home.html")


@reports_access_required
def sales_report(request):
    period, start_date, end_date = parse_date_filters(request, default_period="7")

    sales = Sale.objects.select_related("cashier", "branch").prefetch_related("items__product")

    if start_date and end_date:
        sales = sales.filter(
            sale_date__date__gte=start_date,
            sale_date__date__lte=end_date,
        )

    sales, branches, branch_id = get_branches_and_filter(request, sales)

    user_model = get_user_model()
    cashiers = user_model.objects.filter(
        role__role_name="Cashier",
        is_active=True,
    ).order_by("username")

    if not request.user.has_role(OWNER):
        cashiers = cashiers.filter(branch=request.user.branch)
    elif isinstance(branch_id, int):
        cashiers = cashiers.filter(branch_id=branch_id)

    cashier_id = request.GET.get("cashier", "")
    if cashier_id.isdigit():
        sales = sales.filter(cashier_id=int(cashier_id))

    sales_list = list(sales.order_by("-sale_date"))
    total_revenue = 0
    total_stock_cost = 0

    for sale in sales_list:
        sale.stock_cost = sum(
            item.quantity * item.product.cost_price
            for item in sale.items.all()
        )
        sale.gross_profit = sale.total_amount - sale.stock_cost
        sale.markup_percentage = (
            (sale.gross_profit / sale.stock_cost * 100)
            if sale.stock_cost > 0 else 0
        )
        total_revenue += sale.total_amount
        total_stock_cost += sale.stock_cost

    total_gross_profit = total_revenue - total_stock_cost
    average_markup = (
        (total_gross_profit / total_stock_cost * 100)
        if total_stock_cost > 0 else 0
    )

    return render(
        request,
        "reports/sales_report.html",
        {
            "sales": sales_list,
            "branches": branches,
            "branch_id": branch_id,
            "cashiers": cashiers,
            "cashier_id": cashier_id,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": total_revenue,
            "total_stock_cost": total_stock_cost,
            "total_gross_profit": total_gross_profit,
            "average_markup": average_markup,
            "total_transactions": len(sales_list),
        },
    )


@reports_access_required
def cashier_report(request):
    period, start_date, end_date = parse_date_filters(request, default_period="all")

    sales = Sale.objects.all()

    if start_date and end_date:
        sales = sales.filter(
            sale_date__date__gte=start_date,
            sale_date__date__lte=end_date,
        )

    sales, branches, branch_id = get_branches_and_filter(request, sales)

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
        {
            "cashiers": cashiers,
            "branches": branches,
            "branch_id": branch_id,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@reports_access_required
def inventory_report(request):
    inventory = Inventory.objects.select_related("product", "branch")

    inventory, branches, branch_id = get_branches_and_filter(request, inventory)

    inventory_rows = list(inventory.order_by("product__product_name"))

    total_cost = 0
    total_retail = 0
    total_profit = 0

    for item in inventory_rows:
        item.cost_value = item.quantity * item.product.cost_price
        item.retail_value = item.quantity * item.product.selling_price
        item.gross_profit = item.retail_value - item.cost_value

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
            "branches": branches,
            "branch_id": branch_id,
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
    period, start_date, end_date = parse_date_filters(request, default_period="all")

    orders = PurchaseOrder.objects.select_related(
        "supplier", "branch"
    ).prefetch_related("items")

    if start_date and end_date:
        orders = orders.filter(
            order_date__gte=start_date,
            order_date__lte=end_date,
        )

    orders, branches, branch_id = get_branches_and_filter(request, orders)

    orders_list = list(orders.order_by("-order_date", "-id"))

    supplier_spend = {}
    pending_count = 0
    fulfilled_count = 0
    cancelled_count = 0
    total_fulfilled_spend = 0

    for order in orders_list:
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
            "orders": orders_list,
            "branches": branches,
            "branch_id": branch_id,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
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


@reports_access_required
def export_sales_csv(request):
    period, start_date, end_date = parse_date_filters(request, default_period="7")

    sales = Sale.objects.select_related("cashier", "branch").prefetch_related("items__product")

    if start_date and end_date:
        sales = sales.filter(
            sale_date__date__gte=start_date,
            sale_date__date__lte=end_date,
        )

    sales, _, _ = get_branches_and_filter(request, sales)

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
        "Total Revenue (R)",
        "Stock Cost (R)",
        "Gross Profit (R)",
        "Markup (%)",
    ])

    for sale in sales.order_by("-sale_date"):
        stock_cost = sum(
            item.quantity * item.product.cost_price
            for item in sale.items.all()
        )
        gross_profit = sale.total_amount - stock_cost
        markup_pct = (
            (gross_profit / stock_cost * 100)
            if stock_cost > 0 else 0
        )

        writer.writerow([
            sale.id,
            sale.sale_date.strftime("%Y-%m-%d %H:%M:%S"),
            sale.cashier.username,
            sale.branch.branch_name,
            sale.total_amount,
            stock_cost,
            gross_profit,
            round(markup_pct, 2),
        ])

    return response


@reports_access_required
def export_cashier_csv(request):
    period, start_date, end_date = parse_date_filters(request, default_period="all")

    sales = Sale.objects.all()

    if start_date and end_date:
        sales = sales.filter(
            sale_date__date__gte=start_date,
            sale_date__date__lte=end_date,
        )

    sales, _, _ = get_branches_and_filter(request, sales)

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
    response["Content-Disposition"] = 'attachment; filename="cashier_performance.csv"'

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
    inventory = Inventory.objects.select_related("product", "branch")

    inventory, _, _ = get_branches_and_filter(request, inventory)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory_valuation.csv"'

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
    period, start_date, end_date = parse_date_filters(request, default_period="all")

    orders = PurchaseOrder.objects.select_related(
        "supplier", "branch"
    ).prefetch_related("items")

    if start_date and end_date:
        orders = orders.filter(
            order_date__gte=start_date,
            order_date__lte=end_date,
        )

    orders, _, _ = get_branches_and_filter(request, orders)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="purchasing_report.csv"'

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

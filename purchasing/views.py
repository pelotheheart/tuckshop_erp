from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import ADMIN, OWNER
from accounts.permissions import role_required

from .forms import PurchaseOrderForm, PurchaseOrderItemFormSet, SupplierForm
from .models import PurchaseOrder, Supplier
from .services import OrderNotPending, cancel_purchase_order, fulfil_purchase_order


@role_required(OWNER, ADMIN)
def supplier_list(request):
    # Inactive suppliers are listed too, so they can be reactivated.
    suppliers = Supplier.objects.order_by("supplier_name")
    return render(request, "purchasing/supplier_list.html", {"suppliers": suppliers})


@role_required(OWNER, ADMIN)
def supplier_add(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f"{supplier.supplier_name} was added.")
            return redirect("supplier_list")
    else:
        form = SupplierForm()
    return render(request, "purchasing/supplier_form.html", {"form": form, "title": "Add supplier"})


@role_required(OWNER, ADMIN)
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"{supplier.supplier_name} was updated.")
            return redirect("supplier_list")
    else:
        form = SupplierForm(instance=supplier)
    return render(request, "purchasing/supplier_form.html", {"form": form, "title": "Edit supplier"})


@role_required(OWNER, ADMIN)
@require_POST
def supplier_toggle_active(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    # Phase 2 SRS: a supplier can't be removed while it still has orders waiting to arrive.
    has_pending_orders = supplier.purchaseorder_set.filter(status=PurchaseOrder.Status.PENDING).exists()
    if supplier.is_active and has_pending_orders:
        messages.error(request, f"{supplier.supplier_name} has pending orders, so it can't be deactivated yet.")
    else:
        supplier.is_active = not supplier.is_active
        supplier.save(update_fields=["is_active"])
        state = "reactivated" if supplier.is_active else "deactivated"
        messages.success(request, f"{supplier.supplier_name} was {state}.")
    return redirect("supplier_list")


@role_required(OWNER, ADMIN)
def order_list(request):
    orders = (
        PurchaseOrder.objects.filter(branch=request.user.branch)
        .select_related("supplier")
        .order_by("-order_date", "-id")
    )
    return render(request, "purchasing/order_list.html", {"orders": orders})


@role_required(OWNER, ADMIN)
def order_detail(request, pk):
    order = get_object_or_404(PurchaseOrder.objects.select_related("supplier", "branch"), pk=pk, branch=request.user.branch)
    items = order.items.select_related("product")
    total = sum(item.line_total for item in items)
    return render(request, "purchasing/order_detail.html", {"order": order, "items": items, "total": total})


@role_required(OWNER, ADMIN)
def order_create(request):
    if request.method == "POST":
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseOrderItemFormSet(request.POST)
        # Check both separately, so the user sees every problem at once.
        form_ok = form.is_valid()
        formset_ok = formset.is_valid()
        if form_ok and formset_ok:
            with transaction.atomic():
                order = form.save(commit=False)
                order.branch = request.user.branch
                order.save()
                formset.instance = order
                formset.save()
            messages.success(request, f"Purchase order #{order.id} was created.")
            return redirect("order_detail", pk=order.id)
    else:
        form = PurchaseOrderForm()
        formset = PurchaseOrderItemFormSet()
    return render(request, "purchasing/order_form.html", {"form": form, "formset": formset})


@role_required(OWNER, ADMIN)
@require_POST
def order_fulfil(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk, branch=request.user.branch)
    try:
        fulfil_purchase_order(order.id)
        messages.success(request, f"Order #{order.id} was fulfilled, and its items were added to your stock.")
    except OrderNotPending as error:
        messages.error(request, str(error))
    return redirect("order_detail", pk=order.id)


@role_required(OWNER, ADMIN)
@require_POST
def order_cancel(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk, branch=request.user.branch)
    try:
        cancel_purchase_order(order.id)
        messages.success(request, f"Order #{order.id} was cancelled.")
    except OrderNotPending as error:
        messages.error(request, str(error))
    return redirect("order_detail", pk=order.id)

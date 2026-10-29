from django.db import transaction

from inventory.models import Inventory

from .models import PurchaseOrder


class OrderNotPending(Exception):
    """Raised when someone tries to fulfil or cancel an order that's already been dealt with."""


def fulfil_purchase_order(order_id):
    """Mark a Pending order as Fulfilled and add its items to the branch's stock.

    Phase 3 business rule 4: stock only goes up when an order changes from Pending
    to Fulfilled, and only ever once.
    """
    with transaction.atomic():
        # select_for_update() locks this order until the transaction finishes. If the
        # Fulfil button is clicked twice, the second request waits here, then finds the
        # order is already Fulfilled instead of adding the stock again.
        order = PurchaseOrder.objects.select_for_update().get(pk=order_id)
        if order.status != PurchaseOrder.Status.PENDING:
            raise OrderNotPending(f"Order #{order.id} is already {order.status.lower()}.")

        for item in order.items.select_related("product"):
            # The branch might never have stocked this product before, so make its row if needed.
            stock, created = Inventory.objects.select_for_update().get_or_create(
                branch=order.branch, product=item.product, defaults={"quantity": 0}
            )
            stock.quantity += item.quantity
            stock.save(update_fields=["quantity"])

        order.status = PurchaseOrder.Status.FULFILLED
        order.save(update_fields=["status"])
    return order


def cancel_purchase_order(order_id):
    """Mark a Pending order as Cancelled. Stock isn't touched."""
    with transaction.atomic():
        order = PurchaseOrder.objects.select_for_update().get(pk=order_id)
        if order.status != PurchaseOrder.Status.PENDING:
            raise OrderNotPending(f"Order #{order.id} is already {order.status.lower()}.")
        order.status = PurchaseOrder.Status.CANCELLED
        order.save(update_fields=["status"])
    return order

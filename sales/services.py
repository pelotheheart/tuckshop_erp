from django.db import transaction
from inventory.models import Inventory
from .models import Sale, SaleItem


class SaleRejected(Exception):
    pass


def process_sale(cashier, cart):
    """Save a sale from a list of (product_id, quantity) pairs, or raise SaleRejected and save nothing."""
    if not cart:
        raise SaleRejected("The cart is empty.")
    with transaction.atomic():
        lines = []
        # Locking in product ID order means two tills always lock rows in the same order so they can't deadlock eachother
        for product_id, quantity in sorted(cart):
            stock = (
                Inventory.objects.select_for_update()
                .select_related("product")
                .filter(branch=cashier.branch, product_id=product_id, product__is_active=True)
                .first()
            )
            if stock is None:
                raise SaleRejected("One of the products is no longer sold at this branch.")
            if stock.quantity < quantity:
                raise SaleRejected(f"Not enough {stock.product.product_name} in stock (only {stock.quantity} left).")
            lines.append((stock, quantity))

        sale = Sale.objects.create(branch=cashier.branch, cashier=cashier)
        total = 0
        for stock, quantity in lines:
            price = stock.product.selling_price
            SaleItem.objects.create(sale=sale, product=stock.product, quantity=quantity, selling_price=price)
            stock.quantity -= quantity
            stock.save(update_fields=["quantity"])
            total += price * quantity
        sale.total_amount = total
        sale.save(update_fields=["total_amount"])
    return sale
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from accounts.models import Branch
from inventory.models import Product


class Sale(models.Model):
    """One completed sale: the receipt's header. Its lines are SaleItem rows."""

    id = models.AutoField(primary_key=True, db_column="sale_id")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    # Who rang up the sale. The ERD column is user_id, but in Python we call it cashier, because that's what it means.
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, db_column="user_id")
    sale_date = models.DateTimeField(default=timezone.now)
    # Worked out by the code from the items, never typed in (Phase 3 business rule 2).
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "sale"
        constraints = [
            models.CheckConstraint(condition=Q(total_amount__gte=0), name="ck_sale_total"),
        ]

    def __str__(self):
        return f"Sale #{self.id}"


class SaleItem(models.Model):
    """One line on a receipt: which product, how many, and what it cost at the time."""

    id = models.AutoField(primary_key=True, db_column="sale_item_id")
    # related_name="items" lets us write sale.items.all() to get a sale's lines.
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    # A copy of the product's price when it was sold, so old receipts stay correct after a price change (Phase 3 business rule 3).
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "sale_item"
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="ck_sale_item_quantity"),
            models.CheckConstraint(condition=Q(selling_price__gt=0), name="ck_sale_item_price"),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product}"

    @property
    def line_total(self):
        return self.quantity * self.selling_price
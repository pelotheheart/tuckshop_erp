import datetime

from django.db import models
from django.db.models import Q

from accounts.models import Branch
from inventory.models import Product


class Supplier(models.Model):
    """A company the shop buys stock from."""

    id = models.AutoField(primary_key=True, db_column="supplier_id")
    supplier_name = models.CharField(max_length=100)
    contact_name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    # Suppliers with orders are deactivated, not deleted (Phase 3 section 3.4.5).
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "supplier"
        constraints = [
            # We need at least one way to contact every supplier.
            models.CheckConstraint(
                condition=Q(phone__isnull=False) | Q(email__isnull=False),
                name="ck_supplier_contact",
                violation_error_message="Enter a phone number or an email address (or both).",
            ),
        ]

    def __str__(self):
        return self.supplier_name


class PurchaseOrder(models.Model):
    """An order for stock from one supplier, delivered to one branch."""

    # The only statuses an order can have.
    class Status(models.TextChoices):
        PENDING = "Pending"
        FULFILLED = "Fulfilled"
        CANCELLED = "Cancelled"

    id = models.AutoField(primary_key=True, db_column="purchase_order_id")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    # Today's date, filled in whenever an order is created.
    order_date = models.DateField(default=datetime.date.today)
    # Stock only goes up when an order changes from Pending to Fulfilled (Phase 3 business rule 4).
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    class Meta:
        db_table = "purchase_order"
        constraints = [
            # MySQL itself refuses any other status, like the ENUM in our ERD.
            # These are the same three values as Status above.
            models.CheckConstraint(
                condition=Q(status__in=["Pending", "Fulfilled", "Cancelled"]),
                name="ck_purchase_order_status",
            ),
        ]

    def __str__(self):
        return f"PO #{self.id} from {self.supplier}"


class PurchaseOrderItem(models.Model):
    """One line on a purchase order: which product, how many, and the agreed cost."""

    id = models.AutoField(primary_key=True, db_column="purchase_order_item_id")
    # related_name="items" lets us write order.items.all() to get an order's lines.
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    # The cost agreed with the supplier for this order.
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "purchase_order_item"
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="ck_po_item_quantity"),
            models.CheckConstraint(condition=Q(cost_price__gt=0), name="ck_po_item_cost"),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product}"

    @property
    def line_total(self):
        return self.quantity * self.cost_price
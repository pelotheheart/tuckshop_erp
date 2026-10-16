from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from accounts.models import Branch

# A price has to be at least one cent.
positive_price = MinValueValidator(Decimal("0.01"), "Prices must be more than R0.00.")


class Product(models.Model):
    id = models.AutoField(primary_key=True, db_column="product_id")
    product_name = models.CharField(max_length=100)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[positive_price])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[positive_price])
    minimum_stock = models.IntegerField(default=0, validators=[MinValueValidator(0, "Minimum stock can't be negative.")])
    # We hide old products instead of deleting them for reporting purposes
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "product"
        # Rules MySQL itself checks on every save, no matter where the data comes from.
        constraints = [
            models.CheckConstraint(condition=Q(cost_price__gt=0), name="ck_product_cost_price"),
            models.CheckConstraint(condition=Q(selling_price__gt=0), name="ck_product_selling_price"),
            models.CheckConstraint(condition=Q(minimum_stock__gte=0), name="ck_product_minimum_stock"),
        ]

    def __str__(self):
        return self.product_name


class Inventory(models.Model):
    """How many of one product one branch has. There's one row per product per branch."""

    id = models.AutoField(primary_key=True, db_column="inventory_id")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=0)

    class Meta:
        db_table = "inventory"
        verbose_name_plural = "inventory"
        constraints = [
            # A branch can only have one stock row for each product.
            models.UniqueConstraint(fields=["branch", "product"], name="uq_inventory_branch_product"),
            # Business rule 1 from Phase 3: stock can never go below zero.
            models.CheckConstraint(condition=Q(quantity__gte=0), name="ck_inventory_quantity"),
        ]

    def __str__(self):
        return f"{self.product} at {self.branch}"

    @property
    def is_low_stock(self):
        return self.quantity < self.product.minimum_stock
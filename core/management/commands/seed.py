"""python manage.py seed

Fills an empty database with demo data, so a new teammate has something to look at
straight away: one login per role, a few products with stock at Main Branch, and a
supplier. If the database already has products it does nothing, so it's safe to run twice.
"""

import os
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import ADMIN, CASHIER, OWNER, Branch, Role, User
from inventory.models import Inventory, Product
from purchasing.models import Supplier


class Command(BaseCommand):
    help = "Add demo users, products, stock and a supplier to an empty database."

    # All or nothing: if anything goes wrong halfway through, nothing is left half-added.
    @transaction.atomic
    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write("The database already has products, so nothing was added.")
            return

        password = os.getenv("SEED_PASSWORD", "")
        if len(password) < 8:
            raise CommandError("Set SEED_PASSWORD in your .env file first (at least 8 characters).")

        branch = Branch.objects.get(branch_name="Main Branch")

        # One login per role, all with the password from .env. The owner can also use /admin/.
        for username, role_name in [("owner", OWNER), ("admin", ADMIN), ("cashier", CASHIER)]:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password=password,
                    role=Role.objects.get(role_name=role_name),
                    branch=branch,
                    is_staff=role_name == OWNER,
                    is_superuser=role_name == OWNER,
                )

        # (name, barcode, cost price, selling price, minimum stock, stock at Main Branch)
        products = [
            ("Coca-Cola 330ml", "6001234000011", "8.50", "15.00", 24, 40),
            ("Simba Chips 125g", "6001234000028", "11.00", "18.50", 12, 5),  # below its minimum
            ("White Bread", "6001234000035", "12.00", "17.99", 10, 15),
            ("Fanta 330ml", None, "8.50", "14.00", 10, 30),
        ]
        for name, barcode, cost, price, minimum, quantity in products:
            product = Product.objects.create(
                product_name=name,
                barcode=barcode,
                cost_price=Decimal(cost),
                selling_price=Decimal(price),
                minimum_stock=minimum,
            )
            Inventory.objects.create(branch=branch, product=product, quantity=quantity)

        Supplier.objects.create(supplier_name="Sample Wholesaler", contact_name="Sipho Dube", phone="011 555 1234")

        self.stdout.write(self.style.SUCCESS("Demo data added."))
        self.stdout.write("Log in as owner, admin or cashier, using the SEED_PASSWORD from your .env file.")

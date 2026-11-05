from decimal import Decimal
import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import ADMIN, CASHIER, OWNER, Branch, Role, User
from inventory.models import Inventory, Product
from purchasing.models import PurchaseOrder, PurchaseOrderItem, Supplier
from sales.models import Sale, SaleItem


class ReportsTestCase(TestCase):
    def setUp(self):
        # Fetch or create roles and branches
        self.owner_role, _ = Role.objects.get_or_create(role_name=OWNER)
        self.admin_role, _ = Role.objects.get_or_create(role_name=ADMIN)
        self.cashier_role, _ = Role.objects.get_or_create(role_name=CASHIER)

        self.branch1, _ = Branch.objects.get_or_create(branch_name="Main Branch")
        self.branch2 = Branch.objects.create(branch_name="Secondary Branch")

        self.owner_user = User.objects.create_user(
            username="test_owner",
            password="password123",
            role=self.owner_role,
            branch=self.branch1,
        )
        self.admin_user = User.objects.create_user(
            username="test_admin",
            password="password123",
            role=self.admin_role,
            branch=self.branch1,
        )
        self.cashier1 = User.objects.create_user(
            username="test_cashier1",
            password="password123",
            role=self.cashier_role,
            branch=self.branch1,
        )
        self.cashier2 = User.objects.create_user(
            username="test_cashier2",
            password="password123",
            role=self.cashier_role,
            branch=self.branch2,
        )

        # Products
        self.product1 = Product.objects.create(
            product_name="Product 1",
            cost_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
            minimum_stock=5,
        )
        self.product2 = Product.objects.create(
            product_name="Product 2",
            cost_price=Decimal("20.00"),
            selling_price=Decimal("30.00"),
            minimum_stock=10,
        )

        # Inventory
        self.inv1 = Inventory.objects.create(branch=self.branch1, product=self.product1, quantity=10)
        self.inv2 = Inventory.objects.create(branch=self.branch2, product=self.product2, quantity=2)  # low stock

        # Supplier & PO
        self.supplier = Supplier.objects.create(supplier_name="Supplier A", phone="0111111111")
        self.po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            branch=self.branch1,
            order_date=timezone.now().date(),
            status=PurchaseOrder.Status.FULFILLED,
        )
        PurchaseOrderItem.objects.create(
            purchase_order=self.po,
            product=self.product1,
            quantity=5,
            cost_price=Decimal("10.00"),
        )

        # Sales
        self.sale1 = Sale.objects.create(
            branch=self.branch1,
            cashier=self.cashier1,
            sale_date=timezone.now(),
            total_amount=Decimal("30.00"),
        )
        SaleItem.objects.create(
            sale=self.sale1,
            product=self.product1,
            quantity=2,
            selling_price=Decimal("15.00"),
        )

        self.sale2 = Sale.objects.create(
            branch=self.branch2,
            cashier=self.cashier2,
            sale_date=timezone.now() - datetime.timedelta(days=10),
            total_amount=Decimal("30.00"),
        )
        SaleItem.objects.create(
            sale=self.sale2,
            product=self.product2,
            quantity=1,
            selling_price=Decimal("30.00"),
        )

        self.client = Client()

    def test_access_denied_for_cashier(self):
        self.client.login(username="test_cashier1", password="password123")
        response = self.client.get(reverse("sales_report"))
        self.assertEqual(response.status_code, 403)

    def test_sales_report_statistics_and_row_data(self):
        self.client.login(username="test_owner", password="password123")
        response = self.client.get(reverse("sales_report") + "?period=all")
        self.assertEqual(response.status_code, 200)

        # Total revenue = 30 + 30 = 60
        # Total cost = (2*10) + (1*20) = 20 + 20 = 40
        # Gross profit = 60 - 40 = 20
        # Avg markup % = (20 / 40) * 100 = 50%
        self.assertEqual(response.context["total_revenue"], Decimal("60.00"))
        self.assertEqual(response.context["total_stock_cost"], Decimal("40.00"))
        self.assertEqual(response.context["total_gross_profit"], Decimal("20.00"))
        self.assertEqual(response.context["average_markup"], Decimal("50.00"))
        self.assertEqual(response.context["total_transactions"], 2)

        # Per sale assertions
        sales = response.context["sales"]
        s1 = next(s for s in sales if s.id == self.sale1.id)
        self.assertEqual(s1.stock_cost, Decimal("20.00"))
        self.assertEqual(s1.gross_profit, Decimal("10.00"))
        self.assertEqual(s1.markup_percentage, Decimal("50.00"))

    def test_sales_report_branch_filter(self):
        self.client.login(username="test_owner", password="password123")
        response = self.client.get(reverse("sales_report") + f"?period=all&branch={self.branch1.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_transactions"], 1)

    def test_cashier_report_filtering(self):
        self.client.login(username="test_owner", password="password123")
        response = self.client.get(reverse("cashier_report") + f"?period=all&branch={self.branch1.id}")
        self.assertEqual(response.status_code, 200)
        cashiers = list(response.context["cashiers"])
        self.assertEqual(len(cashiers), 1)
        self.assertEqual(cashiers[0]["cashier__username"], "test_cashier1")

    def test_purchasing_report_filtering(self):
        self.client.login(username="test_owner", password="password123")
        response = self.client.get(reverse("purchasing_report") + f"?period=all&branch={self.branch1.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["fulfilled_count"], 1)
        self.assertEqual(response.context["total_fulfilled_spend"], Decimal("50.00"))

    def test_inventory_report_filtering(self):
        self.client.login(username="test_owner", password="password123")
        response = self.client.get(reverse("inventory_report") + f"?branch={self.branch2.id}")
        self.assertEqual(response.status_code, 200)
        rows = response.context["inventory_rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].product.product_name, "Product 2")
        self.assertEqual(response.context["low_stock_count"], 1)

    def test_csv_exports(self):
        self.client.login(username="test_owner", password="password123")

        # Sales CSV
        r1 = self.client.get(reverse("export_sales_csv") + "?period=all")
        self.assertEqual(r1.status_code, 200)
        self.assertIn("Stock Cost (R)", r1.content.decode("utf-8"))

        # Cashier CSV
        r2 = self.client.get(reverse("export_cashier_csv") + "?period=all")
        self.assertEqual(r2.status_code, 200)

        # Inventory CSV
        r3 = self.client.get(reverse("export_inventory_csv") + f"?branch={self.branch1.id}")
        self.assertEqual(r3.status_code, 200)

        # Purchasing CSV
        r4 = self.client.get(reverse("export_purchasing_csv") + "?period=all")
        self.assertEqual(r4.status_code, 200)

from django.contrib.auth.models import AbstractUser
from django.db import models

# the three roles from our phase 2 SRS, use these names in code
OWNER = "Owner"
ADMIN = 'Administrator'
CASHIER = 'Cashier'

class Role(models.Model):
    id = models.AutoField(primary_key=True, db_column="role_id")
    role_name = models.CharField(max_length=50, unique=True)
    class Meta:
        db_table = "role"
    def __str__(self):
        return self.role_name

class Branch(models.Model):
    id = models.AutoField(primary_key=True,db_column="branch_id")
    branch_name = models.CharField(max_length=100)
    address = models.CharField(max_length=20, null=True, blank=True)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    class Meta:
        db_table = "branch"
        verbose_name_plural = "branches"
    def __str__(self):
        return self.branch_name

class User(AbstractUser):
    # Our ERD calls the key column "user_id", so we name it that in MySQL.
    # In Python it's still just user.id (or user.pk).
    id = models.AutoField(primary_key=True, db_column="user_id")
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    REQUIRED_FIELDS = ["role"]
    def has_role(self, *role_names):
        return self.role.role_name in role_names

    @property
    def is_owner(self):
        return self.has_role(OWNER)

    @property
    def is_administrator(self):
        return self.has_role(ADMIN)

    @property
    def is_cashier(self):
        return self.has_role(CASHIER)
    class Meta:
        # Call the table "user" like the ERD does (Django would call it "accounts_user")
        db_table = "user"

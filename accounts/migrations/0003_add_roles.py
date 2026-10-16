from django.db import migrations


def add_roles(apps, schema_editor):
    # apps.get_model gives us the Role model exactly as it was at this point in history.
    Role = apps.get_model("accounts", "Role")
    for name in ["Owner", "Administrator", "Cashier"]:
        Role.objects.create(role_name=name)


def remove_roles(apps, schema_editor):
    # Lets undo this step if we ever need to go backwards.
    Role = apps.get_model("accounts", "Role")
    Role.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_role"),
    ]

    operations = [
        migrations.RunPython(add_roles, remove_roles),
    ]
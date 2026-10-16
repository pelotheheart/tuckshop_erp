from django.db import migrations


def add_main_branch(apps, schema_editor):
    Branch = apps.get_model("accounts", "Branch")
    Branch.objects.create(branch_name="Main Branch")


def remove_main_branch(apps, schema_editor):
    Branch = apps.get_model("accounts", "Branch")
    Branch.objects.filter(branch_name="Main Branch").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_branch"),
    ]

    operations = [
        migrations.RunPython(add_main_branch, remove_main_branch),
    ]
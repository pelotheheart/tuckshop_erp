from decimal import Decimal

from django import forms

from inventory.models import Product

from .models import PurchaseOrder, PurchaseOrderItem, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["supplier_name", "contact_name", "phone", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["phone"].widget.attrs.update({
            "inputmode": "numeric",
            "maxlength": "10",
            "pattern": "[0-9]{10}",
            "title": "10 digits, numbers only, e.g. 0826492533",
        })

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        # Phone is optional when there's an email, so only check it if something was typed.
        if phone:
            if not phone.isdigit():
                raise forms.ValidationError("Phone number must contain digits only.")
            if len(phone) != 10:
                raise forms.ValidationError("Phone number must contain exactly 10 digits.")
        return phone

def add_bootstrap_classes(form):
    for field in form.fields.values():
        if isinstance(field.widget, forms.Select):
            field.widget.attrs["class"] = "form-select"
        else:
            field.widget.attrs["class"] = "form-control"


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["supplier"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True).order_by("supplier_name")
        add_bootstrap_classes(self)


class PurchaseOrderItemForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1, error_messages={"min_value": "Order at least 1."})
    cost_price = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        error_messages={"min_value": "Cost must be more than R0.00."},
    )

    class Meta:
        model = PurchaseOrderItem
        fields = ["product", "quantity", "cost_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("product_name")
        add_bootstrap_classes(self)


class BaseItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Rows left completely empty are ignored, so check that at least one was filled in.
        if not any(item_form.has_changed() for item_form in self.forms):
            raise forms.ValidationError("Add at least one item to the order.")


PurchaseOrderItemFormSet = forms.inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    formset=BaseItemFormSet,
    extra=1,
    can_delete=False,
)

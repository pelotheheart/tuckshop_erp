from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["product_name", "barcode", "cost_price", "selling_price", "minimum_stock"]

    def __init__(self, *args, **kwargs):
        # Let Django build the form as normal first
        super().__init__(*args, **kwargs)
        # then give every input Bootstrap's "form-control" class so it gets styled.
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
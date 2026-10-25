from django import forms

from .models import User, Branch


class UserRegistrationForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        help_texts = {"username": ""}

    def __init__(self, *args, **kwargs):
        # Let Django build the form as normal first
        super().__init__(*args, **kwargs)
        # then give every input Bootstrap's "form-control" class so it gets styled.
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control", "placeholder": name.replace("_", " ").title()})
            field.required = True  # require user to provide input for all fields on registration
            # customize error message for required fields
            field.error_messages.update({"required": f"{name.replace('_', ' ').title()} is required"})

    def clean(self):
        clean_input = super().clean()
        # Add custom validation for password fields
        password = clean_input.get("password")
        confirm_password = clean_input.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return clean_input


class BranchRegistrationForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ["branch_name", "contact_number", "address"]

    def __init__(self, *args, **kwargs):
        # Let Django build the form as normal first
        super().__init__(*args, **kwargs)
        # then give every input Bootstrap's "form-control" class so it gets styled.
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control", "placeholder": name.replace("_", " ").title()})
            field.required = True  # require user to provide input for all fields on registration
            # customize error message for required fields
            field.error_messages.update({"required": f"{name.replace('_', ' ').title()} is required"})
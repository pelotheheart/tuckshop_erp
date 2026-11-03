from django import forms

from .models import *


class BaseUserForm(forms.ModelForm):
    # All user forms will inherit from the base
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
            # format placeholder text
            field.widget.attrs.update({"class": "form-control", "placeholder": name.replace("_", " ").title()})
            field.required = True  # require user to provide input for all fields on registration
            # customize error message for required fields
            field.error_messages.update({"required": f"{name.replace('_', ' ').title()} is required"})

    def clean(self):
        cleaned_data = super().clean()
        # Add custom validation for password fields, ensures that password & confirm password fields match
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned_data

    def clean_password(self):
        # Ensures that password length is at least 8 characters long
        password = self.cleaned_data["password"]

        if len(password) < 8:
            raise forms.ValidationError("Password must contain at least 8 characters.")

        return password

    def clean_username(self):
        # Add custom username validation, ensures username isn't less than 3 chars long
        username = self.cleaned_data["username"]
        if len(username) < 3:
            raise forms.ValidationError("Username must contain at least 3 characters.")
        return username


class UserRegistrationForm(BaseUserForm):
    # Use BaseUserForm for registration
    pass


class StaffMemberForm(BaseUserForm):
    # Staff Member form inherits BaseUser  and adds Role selection for  Admin & Cashier
    # Choice field depends on user logged in, Owner can manage Admins and Cashiers, Admins can only manage cashiers
    role = forms.ModelChoiceField(queryset=Role.objects.none(), empty_label="Select Role")

    class Meta(BaseUserForm.Meta):
        fields = ["username", "first_name", "last_name"]

    def __init__(self,  *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not current_user:
            return

        if current_user.is_owner:  # Choice field for owner user, can add Admin or Cashier
            self.fields["role"].queryset = Role.objects.filter(role_name__in=[ADMIN, CASHIER])

        elif current_user.is_administrator:  # Choice field for admin user, can add cashier
            self.fields["role"].queryset = Role.objects.filter(role_name=CASHIER)

        for name, field in self.fields.items():
            # format placeholder text
            field.widget.attrs.update({"class": "form-control", "placeholder": name.replace("_", " ").title()})
            field.required = True  # require user to provide input for all fields on registration
            # customize error message for required fields
            field.error_messages.update({"required": f"{name.replace('_', ' ').title()} is required"})


class EditStaffMemberForm(StaffMemberForm):
    # Inherit StaffMember form for editing staff details
    # Limit changes to Username, First Name, Last Name, and Role, password reset handled separately
    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, current_user=current_user, **kwargs)
        self.initial["role"] = self.instance.role  # initialize role selector with current user role
        self.fields.pop("password")  # remove password fields from form
        self.fields.pop("confirm_password")


class ResetPasswordForm(StaffMemberForm):
    # Inherit BaseUser form for resetting staff member password
    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, current_user=current_user, **kwargs)
        # remove all input fields except password and confirm password fields
        self.fields.pop("username")
        self.fields.pop("first_name")
        self.fields.pop("last_name")
        self.fields.pop("role")


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

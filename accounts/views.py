from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render

from .models import User, Branch, Role, ADMIN, OWNER
from .permissions import role_required

from .forms import UserRegistrationForm, BranchRegistrationForm
# Create your views here.


def register(request):
    if request.method == "POST":
        branch_form = BranchRegistrationForm(request.POST)
        user_form = UserRegistrationForm(request.POST)

        if not (branch_form.is_valid() and user_form.is_valid()):
            return render(request, "accounts/register.html", {"user_form": user_form, "branch_form": branch_form})

        # first create branch then create user with for branch link with branch ID
        with transaction.atomic():
            branch = branch_form.save()  # add branch to db

            user = user_form.save(commit=False)  # create user object
            user.set_password(user_form.cleaned_data["password"])  # password hash for db storage
            user.branch = branch  # link user to branch
            user.role = Role.objects.get(role_name=OWNER)  # Add user role, owner by default
            user.save()  # add complete user to db

        # Verify newly created user credentials before creating session
        user = authenticate(username=user_form.cleaned_data.get("username"), password=user_form.cleaned_data.get("password"))

        if user is None:
            return redirect("login") # redirect user to login page if authentication failed

        login(request, user)   # login user and redict them to home page after successful login
        return redirect("home")

    else:
        branch_form = BranchRegistrationForm()
        user_form = UserRegistrationForm()

        return render(request, "accounts/register.html", {"user_form": user_form, "branch_form": branch_form})

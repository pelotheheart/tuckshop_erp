from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render
from datetime import datetime as dt
from .models import User, Branch, Role, ADMIN, OWNER
from .permissions import role_required, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import *
# Create your views here.

now = dt.now().strftime("%H:%m")


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
            return redirect("login")  # redirect user to login page if authentication failed

        login(request, user)   # login user and redict them to home page after successful login
        return redirect("home")

    else:
        branch_form = BranchRegistrationForm()
        user_form = UserRegistrationForm()

        return render(request, "accounts/register.html", {"user_form": user_form, "branch_form": branch_form})


@login_required
@role_required(OWNER, ADMIN)
def staff(request):
    staff_members = []
    # Owner - Get all staff members belonging to Owners branch
    if request.user.is_owner:
        staff_members = (User.objects.filter(branch=request.user.branch).only("first_name", "last_name", "role", "branch")
                         .exclude(username=request.user))

    elif request.user.is_administrator:  # Admin - Get all cashiers belonging to admin users branch
        staff_members = User.objects.filter(branch=request.user.branch, role__role_name=CASHIER)

    return render(request, "accounts/staff.html", {"staff": staff_members, "now": now})


@login_required
@role_required(OWNER, ADMIN)
def add_staff(request):
    # Add new staff member to a branch
    if request.method == "POST":
        member_form = StaffMemberForm(request.POST, current_user=request.user)

        if not member_form.is_valid():
            return render(request, "accounts/add_staff.html", {"member_form": member_form})

        with transaction.atomic():
            new_member = member_form.save(commit=False)  # create member object
            new_member.set_password(member_form.cleaned_data["password"])  # password hash for db storage
            new_member.role = member_form.cleaned_data["role"]
            new_member.branch = request.user.branch  # link user to creators branch

            # get clean branch name for generating user email
            branch_name = request.user.branch.branch_name.lower().replace(" ", "")
            # create user email from username and branch
            new_member.email = f"{new_member.username}@{branch_name}.com"

            new_member.save()  # add new member to db

        messages.success(request, f"{new_member.first_name} {new_member.last_name} was added successfully.")

        return redirect("staff")

    else:
        staff_member_form = StaffMemberForm(current_user=request.user)
        form_header = "Add Staff Member"

        return render(request, "accounts/add_staff.html", {"member_form": staff_member_form,
                                                           "page_title": "Account Registration",
                                                           "form_header": form_header,
                                                           "button_text": "Add Member", "show_password_fields":True,
                                                           "now": now})


@login_required
@role_required(OWNER, ADMIN)
def user_details(request, user_id):
    # Get and manage specific user details
    member = User.objects.get(id=user_id, branch=request.user.branch)
    if request.user.is_administrator and not member.is_cashier:
        raise PermissionDenied  # stop processing if admin tries editing any member other than cashier

    return render(request, "accounts/user_details.html", {"member": member,  "now": now})


@login_required
@role_required(OWNER, ADMIN)
def edit_details(request, user_id):
    # Update staff member details
    member = User.objects.get(id=user_id, branch=request.user.branch)
    page_title = "Edit User"
    form_header = f"Edit {member.username}'s account details"
    btn_text = "Save Changes"

    if request.user.is_administrator and not member.is_cashier:
        raise PermissionDenied  # stop processing if admin tries editing any member other than cashier

    if request.method == "POST":
        # update db with new user details
        form = EditStaffMemberForm(request.POST, instance=member, current_user=request.user)

        if form.is_valid():
            updated_member = form.save(commit=False)  # Update user details in  db
            updated_member.role = form.cleaned_data["role"]
            updated_member.save()
            messages.success(request, f"User {updated_member.username} updated successfully.")

            return redirect("user_details", member.id)

        # redirect to edit details screen with errors displayed
        return render(request, "accounts/add_staff.html", {"member_form": form,
                                                           "form_header": form_header,
                                                           "page_title": page_title,
                                                           "button_text": btn_text,
                                                           "now": now})

    else:
        # Initialize form fields with current user details
        staff_member_form = EditStaffMemberForm(instance=member, current_user=request.user)
        return render(request, "accounts/add_staff.html", {"member_form": staff_member_form,
                                                           "form_header": form_header,
                                                           "page_title": page_title,
                                                           "button_text": btn_text, "now": now})


@login_required
@role_required(OWNER, ADMIN)
def deactivate_user(request, user_id):
    # Deactivate staff member account
    member = User.objects.get(id=user_id, branch=request.user.branch)

    if request.user.is_administrator and not member.is_cashier:
        raise PermissionDenied  # stop processing if admin tries deactivating any member other than cashier

    if request.method == "POST":
        member.is_active = False  # deactivate staff member account
        member.save()

        messages.success(request, f"{member.username} was deactivated successfully.")

        return redirect("staff")

    # Show deactivate confirmation dialog
    return render(request, "accounts/confirm_action.html", {"member": member, "action": "Deactivate"})


@login_required
@role_required(OWNER, ADMIN)
def activate_user(request, user_id):
    # Activate staff member account
    member = User.objects.get(id=user_id, branch=request.user.branch)

    if request.user.is_administrator and not member.is_cashier:
        raise PermissionDenied  # stop processing if admin tries deactivating any member other than cashier

    if request.method == "POST":
        member.is_active = True  # activate staff member account
        member.save()

        messages.success(request, f"{member.username} was activated successfully.")

        return redirect("staff")

    # Show activate confirmation dialog
    return render(request, "accounts/confirm_action.html", {"member": member, "action": "Activate"})


@login_required
@role_required(OWNER, ADMIN)
def reset_password(request, user_id):
    # Reset staff member password
    member = User.objects.get(id=user_id, branch=request.user.branch)

    if request.user.is_administrator and not member.is_cashier:
        raise PermissionDenied  # Stop processing if admin tries changing password for any member other than cashier

    if request.method == "POST":
        form = ResetPasswordForm(request.POST, current_user=request.user)

        if form.is_valid():  # change stored user password
            member.set_password(form.cleaned_data["password"])
            member.save()

            messages.success(request, f"{member.username}'s password was reset successfully.")

            return redirect("user_details", member.id)

        # redirect to reset password page with errors displayed
        return render(request, "accounts/reset_password.html", {"reset_form": form, "member": member})

    return render(request, "accounts/reset_password.html",
                  {"reset_form": ResetPasswordForm(instance=member, current_user=request.user), "member": member})

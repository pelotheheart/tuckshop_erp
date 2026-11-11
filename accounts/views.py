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
    # Check that no owner is registered before registering a new owner

    if User.objects.filter(role__role_name=OWNER).exists():
        return redirect("login")  # redirect to login if owner is already registered

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
    reg_branches = []
    # Owner - Get all staff members belonging to Owners branch
    if request.user.is_owner:
        staff_members = (User.objects.select_related("role", "branch").only("first_name", "last_name", "role", "branch")
                         .exclude(role__role_name=OWNER))
        reg_branches = Branch.objects.all()

    elif request.user.is_administrator:  # Admin - Get all cashiers belonging to admin users branch
        staff_members = User.objects.filter(branch=request.user.branch, role__role_name=CASHIER)

    context = {"staff": staff_members, "branches": reg_branches,  "now": now}
    return render(request, "accounts/staff.html", context)


@login_required
@role_required(OWNER, ADMIN)
def add_staff(request):
    # Add new staff member to a branch
    page_title = "Account Registration"
    form_header = "Add Staff Member"
    button_text = "Add Member"
    pswrd_fields = True
    show_rb = True
    if request.method == "POST":
        member_form = StaffMemberForm(request.POST, current_user=request.user)

        if not member_form.is_valid():
            return render(request, "accounts/add_staff.html", {"member_form": member_form,
                                                               "page_title": page_title,
                                                               "form_header": form_header,
                                                               "button_text": button_text,
                                                               "show_password_fields": pswrd_fields,
                                                               "show_rb": show_rb,
                                                               "now": now})

        with transaction.atomic():
            new_member = member_form.save(commit=False)  # create member object
            new_member.set_password(member_form.cleaned_data["password"])  # password hash for db storage
            new_member.role = member_form.cleaned_data["role"]
            new_member.branch = member_form.cleaned_data["branch"]  # link user to branch selected

            # get clean branch name for generating user email
            selected_branch = member_form.cleaned_data["branch"]
            branch_name = selected_branch.branch_name.lower().replace(" ", "")
            # create user email from username and branch
            new_member.email = f"{new_member.username}@{branch_name}.com".lower()

            new_member.save()  # add new member to db

        messages.success(request, f"{new_member.first_name} {new_member.last_name} was added successfully.")

        return redirect("staff")

    else:
        staff_member_form = StaffMemberForm(current_user=request.user)

        return render(request, "accounts/add_staff.html", {"member_form": staff_member_form,
                                                           "page_title": "Account Registration",
                                                           "form_header": form_header,
                                                           "button_text": button_text, "show_password_fields": pswrd_fields,
                                                           "show_rb": show_rb,
                                                           "now": now})


@login_required
@role_required(OWNER)
def my_profile(request):
    return redirect("user_details", request.user.id)


@login_required
@role_required(OWNER, ADMIN)
def user_details(request, user_id):
    # Get and manage specific user details
    member = User.objects.get(id=user_id)
    if request.user.is_administrator and not member.is_cashier:
        raise PermissionDenied  # stop processing if admin tries editing any member other than cashier

    return render(request, "accounts/user_details.html", {"member": member,  "now": now})


@login_required
@role_required(OWNER)
def edit_my_profile(request):
    # Update owner details
    member = request.user
    page_title = "Edit User"
    form_header = f"Edit {member.username}'s account details"
    btn_text = "Save Changes"
    show_rb = False  # hide role and branch icons
    if request.method == "POST":
        # update db with new owner details
        form = EditMyProfileForm(request.POST, instance=member, current_user=request.user)

        if form.is_valid():
            updated_member = form.save()  # Update user details in  db
            messages.success(request, f"User {updated_member.username} updated successfully.")

            return redirect("user_details", member.id)

        # redirect to edit details screen with errors displayed
        return render(request, "accounts/add_staff.html", {"member_form": form,
                                                           "form_header": form_header,
                                                           "page_title": page_title,
                                                           "button_text": btn_text,
                                                           "show_rb": show_rb,
                                                           "now": now})

    else:
        # Initialize form fields with owner details
        staff_member_form = EditMyProfileForm(instance=member, current_user=request.user)
        return render(request, "accounts/add_staff.html", {"member_form": staff_member_form,
                                                           "form_header": form_header,
                                                           "page_title": page_title,
                                                           "button_text": btn_text,
                                                           "show_rb": show_rb,
                                                           "now": now})


@login_required
@role_required(OWNER, ADMIN)
def edit_details(request, user_id):
    # Update staff member details
    member = User.objects.get(id=user_id)
    page_title = "Edit User"
    form_header = f"Edit {member.username}'s account details"
    btn_text = "Save Changes"
    show_rb = True  # show role and branch icons
    if request.user.is_administrator and not member.is_cashier:
        raise PermissionDenied  # stop processing if admin tries editing any member other than cashier

    if request.method == "POST":
        # update db with new user details
        form = EditStaffMemberForm(request.POST, instance=member, current_user=request.user)

        if form.is_valid():
            updated_member = form.save(commit=False)  # Update user details in  db
            updated_member.role = form.cleaned_data["role"]
            updated_member.branch = form.cleaned_data["branch"]  # link user to branch selected
            updated_member.save()
            messages.success(request, f"User {updated_member.username} updated successfully.")

            return redirect("user_details", member.id)

        # redirect to edit details screen with errors displayed
        return render(request, "accounts/add_staff.html", {"member_form": form,
                                                           "form_header": form_header,
                                                           "page_title": page_title,
                                                           "button_text": btn_text,
                                                           "show_rb": show_rb,
                                                           "now": now})

    else:
        # Initialize form fields with current user details
        staff_member_form = EditStaffMemberForm(instance=member, current_user=request.user)
        return render(request, "accounts/add_staff.html", {"member_form": staff_member_form,
                                                           "form_header": form_header,
                                                           "page_title": page_title,
                                                           "button_text": btn_text,
                                                           "show_rb": show_rb,
                                                           "now": now})


@login_required
@role_required(OWNER, ADMIN)
def deactivate_user(request, user_id):
    # Deactivate staff member account
    member = User.objects.get(id=user_id)

    if request.user.is_administrator and not member.is_cashier:
        raise PermissionDenied  # stop processing if admin tries deactivating any member other than cashier

    if member == request.user:  # prevent owners and admins from deactivating their own accounts
        messages.error(request, "You cannot deactivate your own account.")

        return redirect("user_details", member.id)

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
    member = User.objects.get(id=user_id)

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
    member = User.objects.get(id=user_id)

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


@login_required
@role_required(OWNER)
def branches(request):
    # Owner - Get all registered branches
    registered_branches = Branch.objects.all()

    return render(request, "accounts/branches.html", {"branches": registered_branches, "now": now})


@login_required
@role_required(OWNER)
def add_branch(request):
    # Add new branch in db
    page_title = "New Branch Registration"
    form_header = "Add New Branch"
    button_text = "Add Branch"

    if request.method == "POST":
        branch_form = BranchRegistrationForm(request.POST)

        if not branch_form.is_valid():
            return render(request, "accounts/add_branch.html", {"branch_form": branch_form,
                                                                "page_title": page_title,
                                                                "form_header": form_header,
                                                                "button_text": button_text,
                                                                "now": now
                                                                })

        new_branch = branch_form.save()  # save branch

        messages.success(request, f"Branch '{new_branch.branch_name}' added successfully.")

        return redirect("branches")

    else:
        branch_form = BranchRegistrationForm()

        return render(request, "accounts/add_branch.html", {"branch_form": branch_form,
                                                            "page_title": page_title,
                                                            "form_header": form_header,
                                                            "button_text": button_text,
                                                            "now": now})


@login_required
@role_required(OWNER)
def edit_branch(request, branch_id):
    # Update branch details
    reg_branch = Branch.objects.get(id=branch_id)
    page_title = "Edit Branch"
    form_header = f"Change {reg_branch.branch_name} branch details"
    btn_text = "Save Changes"

    if request.method == "POST":
        # update db with new branch details
        form = BranchRegistrationForm(request.POST, instance=reg_branch)

        if form.is_valid():
            updated_branch = form.save()
            messages.success(request, f"Branch '{updated_branch.branch_name}' updated successfully.")

            return redirect("branches")

        # redirect to edit branch details screen with errors displayed
        return render(request, "accounts/add_branch.html", {"branch_form": form,
                                                            "form_header": form_header,
                                                            "page_title": page_title,
                                                            "button_text": btn_text,
                                                            "now": now})

    else:
        # Initialize form fields with current branch details
        branch_form = BranchRegistrationForm(instance=reg_branch)
        return render(request, "accounts/add_branch.html", {"branch_form": branch_form,
                                                            "form_header": form_header,
                                                            "page_title": page_title,
                                                            "button_text": btn_text, "now": now})

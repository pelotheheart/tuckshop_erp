from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def role_required(*role_names):
    """Only let users with one of the roles open the page e.g. @role_required(OWNER,ADMIN)"""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.has_role(*role_names):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
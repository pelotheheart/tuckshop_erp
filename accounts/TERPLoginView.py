from django.contrib.auth.views import LoginView
from .models import *


class TERPLoginView(LoginView):
    # Inherit from Django's built-in LoginView, to customize login page
    # hides registration link if Owner is already registered

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        # Add context, owner_registered is true if an owner exists
        # Used in login template to hide registration link
        context["owner_registered"] = User.objects.filter(role__role_name=OWNER).exists()

        return context

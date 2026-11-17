from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChange:
    """Demo hisoblar uchun parolni almashtirishni majburlaydi."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        u = request.user
        if u.is_authenticated and u.must_change_password:
            allowed = (reverse("password_change"), reverse("logout"))
            if request.path not in allowed and not request.path.startswith("/static/"):
                return redirect("password_change")
        return self.get_response(request)

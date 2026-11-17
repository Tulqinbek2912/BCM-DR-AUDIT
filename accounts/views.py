from django.contrib import messages
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from .forms import LoginForm, PwForm
from .utils import log


class CustomLogin(LoginView):
    template_name = "login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class ChangePassword(PasswordChangeView):
    template_name = "password_change.html"
    form_class = PwForm
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        resp = super().form_valid(form)
        u = self.request.user
        if u.must_change_password:
            u.must_change_password = False
            u.save(update_fields=["must_change_password"])
        log(u, "Foydalanuvchi faoliyati", "Parolni almashtirdi", self.request)
        messages.success(self.request, "Parol muvaffaqiyatli almashtirildi.")
        return resp

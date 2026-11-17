from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import User


class BootstrapMixin:
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        for f in self.fields.values():
            w = f.widget
            if isinstance(f, forms.DateTimeField):
                f.widget = w = forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")
                f.input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
            elif isinstance(f, forms.DateField):
                f.widget = w = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
                f.input_formats = ["%Y-%m-%d", "%d.%m.%Y"]
            if isinstance(w, forms.CheckboxInput):
                cls = "form-check-input"
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                cls = "form-select"
            elif isinstance(w, forms.ClearableFileInput):
                cls = "form-control"
            else:
                cls = "form-control"
            w.attrs["class"] = (w.attrs.get("class", "") + " " + cls).strip()
            if isinstance(w, forms.Textarea):
                w.attrs.setdefault("rows", 3)


class LoginForm(BootstrapMixin, AuthenticationForm):
    username = forms.CharField(label="Foydalanuvchi nomi")
    password = forms.CharField(label="Parol", widget=forms.PasswordInput)
    error_messages = {
        "invalid_login": "Foydalanuvchi nomi yoki parol noto‘g‘ri.",
        "inactive": "Bu hisob faol emas.",
    }


class PwForm(BootstrapMixin, PasswordChangeForm):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["old_password"].label = "Joriy parol"
        self.fields["new_password1"].label = "Yangi parol"
        self.fields["new_password2"].label = "Yangi parolni takrorlang"
        self.error_messages["password_incorrect"] = "Joriy parol noto‘g‘ri."
        self.error_messages["password_mismatch"] = "Kiritilgan parollar mos kelmadi."


class UserForm(BootstrapMixin, forms.ModelForm):
    password = forms.CharField(label="Parol", required=False, widget=forms.PasswordInput(render_value=False),
                               help_text="Tahrirlashda bo‘sh qoldirilsa, parol o‘zgarmaydi.")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "is_active",
                  "must_change_password", "password"]
        labels = {"username": "Foydalanuvchi nomi", "first_name": "Ism", "last_name": "Familiya",
                  "email": "Elektron pochta", "role": "Rol", "is_active": "Faol"}

    def clean(self):
        d = super().clean()
        pw = d.get("password")
        if not self.instance.pk and not pw:
            self.add_error("password", "Yangi foydalanuvchi uchun parol kiritilishi shart.")
        if pw:
            try:
                password_validation.validate_password(pw, self.instance)
            except forms.ValidationError as e:
                self.add_error("password", e)
        return d

    def save(self, commit=True):
        u = super().save(commit=False)
        if self.cleaned_data.get("password"):
            u.set_password(self.cleaned_data["password"])
        if commit:
            u.save()
        return u

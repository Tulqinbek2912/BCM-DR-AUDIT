from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLES = [("admin", "Administrator"), ("auditor", "Axborot xavfsizligi auditori"),
             ("manager", "Tashkilot menejeri"), ("viewer", "Kuzatuvchi")]
    role = models.CharField("Rol", max_length=10, choices=ROLES, default="viewer")
    must_change_password = models.BooleanField("Parolni almashtirish shart", default=False)

    @property
    def role_key(self):
        return "admin" if self.is_superuser else self.role

    @property
    def role_label(self):
        return dict(self.ROLES).get(self.role_key, self.role)


class ActivityLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Foydalanuvchi")
    category = models.CharField("Turi", max_length=40)
    message = models.CharField("Tavsif", max_length=500)
    ip = models.GenericIPAddressField("IP manzil", null=True, blank=True)
    created_at = models.DateTimeField("Vaqt", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Faoliyat jurnali"

    def __str__(self):
        return f"{self.category}: {self.message}"

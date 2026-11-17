from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("kirish/", views.CustomLogin.as_view(), name="login"),
    path("chiqish/", LogoutView.as_view(), name="logout"),
    path("parol/", views.ChangePassword.as_view(), name="password_change"),
]

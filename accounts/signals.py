from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .utils import log


@receiver(user_logged_in)
def _in(sender, request, user, **kw):
    log(user, "Kirish", "Tizimga muvaffaqiyatli kirdi", request)


@receiver(user_logged_out)
def _out(sender, request, user, **kw):
    if user:
        log(user, "Kirish", "Tizimdan chiqdi", request)


@receiver(user_login_failed)
def _fail(sender, credentials, request=None, **kw):
    log(None, "Kirish", f"Muvaffaqiyatsiz kirish urinishi: «{credentials.get('username', '')}»", request)

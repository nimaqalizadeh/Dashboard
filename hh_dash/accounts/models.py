from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_('email address'), blank=False)
    phone = models.CharField('Phone Number', max_length=11)


    def __str__(self):
        return f"{self.username}"

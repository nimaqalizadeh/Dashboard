from django.contrib import admin
from . import models


class AccountAdmin(admin.ModelAdmin):
    ...


admin.site.register(models.User, AccountAdmin)

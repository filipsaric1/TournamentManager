from django.contrib import admin

# Register your models here.
from .models import User, Tournament

admin.site.register(User)
admin.site.register(Tournament)

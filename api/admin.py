from django.contrib import admin

from api.models import Blog, User

admin.site.register(User)
admin.site.register(Blog)

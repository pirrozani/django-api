import datetime
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class User(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    password = models.CharField(max_length=256, validators=[MinLengthValidator(6)])
    email = models.EmailField(max_length=254, unique=True)
    register_at = models.DateField(default=datetime.date.today, editable=False)
    # The login account that writes as this author; seeded authors have none
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='author',
    )

    class Meta:
        # Newest first; id breaks ties between users registered on the same day
        ordering = ['-register_at', '-id']

    def __str__(self):
        return self.first_name + ' ' + self.last_name

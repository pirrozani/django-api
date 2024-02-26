from django.core.validators import MinLengthValidator
from django.db import models
import datetime


class User(models.Model):
    DoesNotExist = None
    objects = None
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    password = models.CharField(max_length=256, validators=[MinLengthValidator(6)])
    email = models.EmailField(max_length=254, unique=True)
    register_at = models.DateField(default=datetime.date.today, editable=False)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

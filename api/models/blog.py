import datetime
from django.db import models
from .user import User


class Blog(models.Model):
    DoesNotExist = None
    objects = None
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateField(default=datetime.date.today, editable=False)

    def __str__(self):
        return self.title

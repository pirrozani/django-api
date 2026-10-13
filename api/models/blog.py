import datetime

from django.db import models

from .user import User


class Blog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateField(default=datetime.date.today, editable=False)

    class Meta:
        # Newest first; id breaks ties between blogs created on the same day
        ordering = ['-created_at', '-id']

    def __str__(self):
        return self.title

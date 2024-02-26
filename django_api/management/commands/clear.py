from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps
from api.models import User


class Command(BaseCommand):
    help = 'Clear the User table and reset its auto-increment index'

    def handle(self, *args, **options):
        self.clear_data_and_reset_index()

    def clear_data_and_reset_index(self):
        user_model = apps.get_model('api', 'User')
        with transaction.atomic():
            user_model.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(
                'Successfully clear the Users table and reset its auto-increment index.')
            )

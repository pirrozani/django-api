from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps
from django.db import connection

class Command(BaseCommand):
    help = 'Clear the User table and reset its auto-increment index'

    # Reset the auto-increment index for the given model
    def reset_sequence(self, model):
        table_name = model._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")

    def handle(self, *args, **options):
        self.clear_data_and_reset_index()

    # Clear the User table and reset its auto-increment index
    def clear_data_and_reset_index(self):
        user_model = apps.get_model('api', 'User')
        blog_model = apps.get_model('api', 'Blog')
        
        with transaction.atomic():
            user_model.objects.all().delete()
            self.reset_sequence(user_model)

            blog_model.objects.all().delete()
            self.reset_sequence(blog_model)
        
        self.stdout.write(self.style.SUCCESS(
            'Successfully clear and reset auto-increment index for each table.')
        )

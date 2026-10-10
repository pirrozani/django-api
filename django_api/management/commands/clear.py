from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction


# Empty the models' tables and restart their id sequences at 1, on any database backend.
# Postgres gets TRUNCATE ... RESTART IDENTITY, which rolls back with the transaction
# (a separate setval() would not); SQLite gets DELETE plus a sqlite_sequence reset.
def flush_tables(*models):
    # Fire pending deferred FK checks first: Postgres refuses to TRUNCATE a table with
    # pending trigger events from rows inserted earlier in the same transaction
    if connection.vendor == 'postgresql':
        connection.check_constraints()
    statements = connection.ops.sql_flush(
        no_style(),
        [m._meta.db_table for m in models],
        reset_sequences=True,
    )
    connection.ops.execute_sql_flush(statements)


class Command(BaseCommand):
    help = 'Clear the User and Blog tables and reset their id sequences'

    # Clear every demo table
    def handle(self, *args, **options):
        self.clear_data_and_reset_index()

    # Empty blogs, then users, and restart both id sequences at 1
    def clear_data_and_reset_index(self):
        user_model = apps.get_model('api', 'User')
        blog_model = apps.get_model('api', 'Blog')

        with transaction.atomic():
            flush_tables(blog_model, user_model)

        self.stdout.write(self.style.SUCCESS(
            'Successfully clear and reset auto-increment index for each table.')
        )

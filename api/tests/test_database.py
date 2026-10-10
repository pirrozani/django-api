import os
import runpy
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from api.models import User
from django_api.management.commands.clear import flush_tables

SETTINGS_FILE = Path(settings.BASE_DIR) / 'django_api' / 'settings.py'


class DatabaseSettingsTests(SimpleTestCase):
    # Evaluate settings.py with only the given environment, ignoring the local .env
    def load_settings(self, **environ):
        with patch.dict(os.environ, {'SECRET_KEY': 'test', **environ}, clear=True):
            with patch('environ.Env.read_env'):
                return runpy.run_path(str(SETTINGS_FILE))['DATABASES']['default']

    # Without DATABASE_URL the app keeps using db.sqlite3 (#5)
    def test_sqlite_without_database_url(self):
        db = self.load_settings()
        self.assertEqual(db['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(Path(db['NAME']), Path(settings.BASE_DIR) / 'db.sqlite3')

    # A Postgres DATABASE_URL selects the Postgres backend and keeps its options
    def test_postgres_database_url(self):
        db = self.load_settings(
            DATABASE_URL='postgresql://u:p@db.example.com:5432/demo?sslmode=require'
        )
        self.assertEqual(db['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(db['NAME'], 'demo')
        self.assertEqual(db['HOST'], 'db.example.com')
        self.assertEqual(db['OPTIONS'], {'sslmode': 'require'})

    # Persistent connections are health-checked; CONN_MAX_AGE is configurable
    def test_connection_settings(self):
        self.assertEqual(self.load_settings()['CONN_MAX_AGE'], 60)
        db = self.load_settings(CONN_MAX_AGE='0')
        self.assertEqual(db['CONN_MAX_AGE'], 0)
        self.assertTrue(db['CONN_HEALTH_CHECKS'])


class PopulateMobileLengthTests(TestCase):
    # Fake mobiles fit max_length=20, which Postgres enforces and SQLite does not
    def test_fake_mobiles_fit_the_column(self):
        call_command('populate', users=50, articles=0, stdout=StringIO())
        max_length = User._meta.get_field('mobile').max_length
        for mobile in User.objects.values_list('mobile', flat=True):
            self.assertLessEqual(len(mobile), max_length)


@patch('django_api.management.commands.clear.connection')
class FlushTablesTests(SimpleTestCase):
    # On Postgres, pending deferred FK checks fire before the TRUNCATE
    def test_postgres_checks_constraints_before_flush(self, connection):
        connection.vendor = 'postgresql'
        calls = []
        connection.check_constraints.side_effect = lambda: calls.append('check')
        connection.ops.execute_sql_flush.side_effect = lambda _: calls.append('flush')

        flush_tables(User)

        self.assertEqual(calls, ['check', 'flush'])

    # Other backends skip the check (SQLite would scan every table for orphans)
    def test_sqlite_skips_constraint_check(self, connection):
        connection.vendor = 'sqlite'

        flush_tables(User)

        connection.check_constraints.assert_not_called()
        connection.ops.execute_sql_flush.assert_called_once()

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from api.models import Blog, User
from django_api.management.commands.populate import Command as PopulateCommand


class ManagementCommandTests(TestCase):
    # Run a management command with its output captured
    def run_command(self, *args, **options):
        call_command(*args, stdout=StringIO(), **options)

    # clear removes every row and the next ids start at 1 again (#6)
    def test_clear_then_populate_restarts_ids_at_1(self):
        self.run_command('populate', users=3, articles=4)
        self.run_command('clear')
        self.assertFalse(User.objects.exists())
        self.assertFalse(Blog.objects.exists())

        self.run_command('populate', users=2, articles=3)
        self.assertEqual(sorted(User.objects.values_list('id', flat=True)), [1, 2])
        self.assertEqual(sorted(Blog.objects.values_list('id', flat=True)), [1, 2, 3])

    # populate refuses to create articles when there are no users to own them
    def test_populate_articles_without_users_raises_command_error(self):
        with self.assertRaisesMessage(CommandError, 'without users'):
            self.run_command('populate', users=0, articles=5)
        self.assertFalse(Blog.objects.exists())

    # populate can add articles to users that already exist
    def test_populate_articles_with_existing_users(self):
        self.run_command('populate', users=2, articles=0)
        self.run_command('populate', users=0, articles=3)
        self.assertEqual(Blog.objects.count(), 3)

    # reset_demo leaves exactly the demo row counts, with ids from 1
    def test_reset_demo_leaves_30_users_and_80_blogs(self):
        self.run_command('populate', users=5, articles=5)
        self.run_command('reset_demo')
        self.assertEqual(User.objects.count(), 30)
        self.assertEqual(Blog.objects.count(), 80)
        self.assertEqual(User.objects.order_by('id').first().id, 1)

    # A failing reset_demo rolls back the clear, and new rows still get fresh ids
    def test_reset_demo_failure_keeps_old_data_and_sequences(self):
        self.run_command('populate', users=3, articles=4)
        user_ids = sorted(User.objects.values_list('id', flat=True))
        blog_ids = sorted(Blog.objects.values_list('id', flat=True))

        with patch.object(
            PopulateCommand, 'populate_fake_blog_data', side_effect=RuntimeError('boom')
        ):
            with self.assertRaises(RuntimeError):
                self.run_command('reset_demo')

        self.assertEqual(sorted(User.objects.values_list('id', flat=True)), user_ids)
        self.assertEqual(sorted(Blog.objects.values_list('id', flat=True)), blog_ids)
        self.run_command('populate', users=1, articles=1)
        self.assertEqual(User.objects.count(), 4)
        self.assertEqual(Blog.objects.count(), 5)

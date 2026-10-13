from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

DEMO_USERS = 30
DEMO_ARTICLES = 80


class Command(BaseCommand):
    help = (
        f'Reset the demo data: clear, then populate {DEMO_USERS} users '
        f'and {DEMO_ARTICLES} blogs, and create the demo login account'
    )

    # Clear, repopulate and create the demo login in one transaction, so a failure
    # leaves the old data in place
    def handle(self, *args, **options):
        with transaction.atomic():
            call_command('clear', stdout=self.stdout)
            call_command('populate', users=DEMO_USERS, articles=DEMO_ARTICLES, stdout=self.stdout)
            call_command('create_demo_user', stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS('Successfully reset the demo data.'))

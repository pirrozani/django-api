from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User as Account
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rest_framework.authtoken.models import Token

from api.models import User as Author


class Command(BaseCommand):
    help = (
        'Create or update the demo login account from DEMO_USERNAME / DEMO_PASSWORD, '
        'with its own author profile. Safe to run repeatedly; the token comes from the '
        'post_save signal'
    )

    # Create the account if missing, then (re)set its password
    def handle(self, *args, **options):
        username = settings.DEMO_USERNAME
        password = settings.DEMO_PASSWORD
        if not username or not password:
            raise CommandError('Set DEMO_USERNAME and DEMO_PASSWORD to create the demo user.')

        with transaction.atomic():
            account, created = Account.objects.get_or_create(username=username)
            # Never reset an admin's password through the demo settings
            if account.is_staff or account.is_superuser:
                raise CommandError(f'"{username}" is a staff account; pick another DEMO_USERNAME.')
            password_changed = created or not account.check_password(password)
            # An account deactivated in the admin can't log in, so the demo login would 400
            changed = password_changed or not account.is_active
            if changed:
                account.is_active = True
                account.set_password(password)
                account.save()
            # A new password revokes the old token, so its holders lose write access.
            # An unchanged password keeps it, so nightly resets don't log visitors out
            if password_changed and not created:
                Token.objects.filter(user=account).delete()
                Token.objects.create(user=account)
            # The demo account writes as its own author, which owns no seeded blogs, so
            # it can only change the blogs it creates
            email = f'{username}@demo.invalid'
            author_created = not Author.objects.filter(account=account).exists()
            if author_created:
                # email is unique; refuse rather than take over another author's profile
                if Author.objects.filter(email=email).exists():
                    raise CommandError(
                        f'An author with email "{email}" already exists; delete it or pick another DEMO_USERNAME.'
                    )
                Author.objects.create(
                    account=account,
                    first_name='Demo',
                    last_name='Account',
                    username=username,
                    email=email,
                    password=make_password(None),
                )

        action = 'Created' if created else ('Updated' if changed else 'Unchanged')
        self.stdout.write(self.style.SUCCESS(f'{action} demo user "{username}".'))
        if author_created:
            self.stdout.write(self.style.SUCCESS(f'Created author profile for "{username}".'))

from django.conf import settings
from django.contrib.auth.models import User as Account
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = (
        'Create or update the demo login account from DEMO_USERNAME / DEMO_PASSWORD. '
        'Safe to run repeatedly; the token comes from the post_save signal'
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
                raise CommandError(
                    f'"{username}" is a staff account; pick another DEMO_USERNAME.'
                )
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

        action = 'Created' if created else ('Updated' if changed else 'Unchanged')
        self.stdout.write(self.style.SUCCESS(f'{action} demo user "{username}".'))

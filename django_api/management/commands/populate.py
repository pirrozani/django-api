from django.core.management.base import BaseCommand
from faker import Faker
from api.models import User


class Command(BaseCommand):
    help = 'Populates the database with fake data...'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, default=10, help='The number of fake users to create')

    def handle(self, *args, **options):
        count = options['count']
        self.populate_fake_user_data(count)

    def populate_fake_user_data(self, count):
        faker = Faker()
        for _ in range(count):
            User.objects.create(
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                mobile=faker.phone_number(),
                username=faker.user_name(),
                email=faker.email(),
                password=faker.md5(),
                register_at=faker.date()
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} fake users.'))

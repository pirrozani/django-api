from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from faker import Faker
from api.models import User, Blog


class Command(BaseCommand):
    help = 'Populates the database with fake data...'

    # Add command line arguments
    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=100, help='The number of fake users to create')
        parser.add_argument('--articles', type=int, default=200, help='The number of fake articles to create')

    def handle(self, *args, **options):
        user_count = options.get('users', 100)
        self.populate_fake_user_data(user_count)

        blog_count = options.get('articles', 200)
        self.populate_fake_blog_data(blog_count)

    # Populate the User table with fake data
    def populate_fake_user_data(self, count):
        faker = Faker()
        for _ in range(count):
            User.objects.create(
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                mobile=faker.phone_number(),
                username=faker.user_name(),
                email=faker.email(),
                password=make_password(faker.password(), None, 'pbkdf2_sha256'),
                register_at=faker.date()
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} fake users.'))

    # Populate the Blog table with fake data
    def populate_fake_blog_data(self, count):
        faker = Faker()
        for _ in range(count):
            user = User.objects.order_by('?').first()
            Blog.objects.create(
                title=faker.sentence(),
                content=faker.text(),
                user_id=user.id,
                created_at=faker.date()
            )
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} fake Articles.'))

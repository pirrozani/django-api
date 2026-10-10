from io import StringIO

import django
from django.contrib.auth.models import User as Account
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.authtoken.models import Token

from api.models import Blog, User

API_PATHS = {
    '/api/users/': {'get', 'post'},
    '/api/users/{user_id}': {'get', 'put', 'patch', 'delete'},
    '/api/blogs/': {'get', 'post'},
    '/api/blogs/{blog_id}': {'get', 'put', 'delete'},
    '/api/blogs/user/{user_id}': {'get'},
}


class DependencyUpgradeTests(TestCase):
    # The project runs on the Django 5.2 LTS series (#4)
    def test_django_is_5_2_lts(self):
        self.assertEqual(django.VERSION[:2], (5, 2))

    # Swagger UI loads on the upgraded drf-spectacular
    def test_swagger_ui_loads(self):
        response = self.client.get(reverse('swagger-ui'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'swagger-ui')

    # The generated schema lists every API endpoint and method
    def test_schema_lists_every_endpoint(self):
        response = self.client.get(reverse('schema'), {'format': 'json'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        paths = response.json()['paths']
        for path, methods in API_PATHS.items():
            with self.subTest(path=path):
                self.assertIn(path, paths)
                self.assertTrue(methods <= set(paths[path]))

    # Creating a login account issues a token that authenticates requests
    def test_token_authentication(self):
        account = Account.objects.create_user('reader', password='secret-123')
        token = Token.objects.get(user=account)
        response = self.client.get(
            reverse('user-list'), HTTP_AUTHORIZATION=f'Token {token.key}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # populate still works with the upgraded Faker
    def test_populate_creates_fake_data(self):
        Faker.seed(4)
        call_command('populate', users=3, articles=5, stdout=StringIO())
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Blog.objects.count(), 5)

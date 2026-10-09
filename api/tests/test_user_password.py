from importlib import import_module

from django.apps import apps
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User as Account
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.models import User

hash_migration = import_module('api.migrations.0003_hash_plain_text_passwords')

NEW_USER = {
    'first_name': 'Robert',
    'last_name': 'Oliver',
    'username': 'lyang',
    'mobile': '(482)598-4678',
    'password': 'secret-123',
    'email': 'robert@example.com',
}


class UserPasswordTests(TestCase):
    # Create an author and log the client in with an auth account
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(Account.objects.create_user('demo', password='x'))
        self.user = User.objects.create(
            first_name='Ann', last_name='Lee', username='alee', email='ann@example.com',
            password='pbkdf2_sha256$1$salt$hash',
        )
        self.detail_url = reverse('user-detail', args=[self.user.id])

    # Check that a response body never carries a password field
    def assertNoPassword(self, response):
        self.assertNotIn('password', response.content.decode())

    # Check that the stored password is a PBKDF2 hash of the given raw value
    def assertHashed(self, user_id, raw):
        stored = User.objects.get(pk=user_id).password
        self.assertTrue(stored.startswith('pbkdf2_sha256$'), stored)
        self.assertTrue(check_password(raw, stored))

    # Reading users never exposes the password
    def test_list_and_detail_hide_password(self):
        self.assertNoPassword(self.client.get(reverse('user-list')))
        self.assertNoPassword(self.client.get(self.detail_url))

    # Creating a user stores a hash and hides it in the response
    def test_post_hashes_password_and_hides_it(self):
        response = self.client.post(reverse('user-list'), NEW_USER, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNoPassword(response)
        self.assertHashed(User.objects.get(email=NEW_USER['email']).id, NEW_USER['password'])

    # A new user must come with a password
    def test_post_requires_password(self):
        data = {k: v for k, v in NEW_USER.items() if k != 'password'}
        response = self.client.post(reverse('user-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(email=NEW_USER['email']).exists())

    # A full update with a password stores a new hash
    def test_put_hashes_password_and_hides_it(self):
        response = self.client.put(self.detail_url, NEW_USER, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNoPassword(response)
        self.assertHashed(self.user.id, NEW_USER['password'])

    # A full update without a password keeps the stored one
    def test_put_without_password_keeps_it(self):
        old_password = self.user.password
        data = {k: v for k, v in NEW_USER.items() if k != 'password'}
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNoPassword(response)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, NEW_USER['first_name'])
        self.assertEqual(self.user.password, old_password)

    # A partial update with a password stores a new hash
    def test_patch_hashes_password(self):
        response = self.client.patch(self.detail_url, {'password': 'other-456'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNoPassword(response)
        self.assertHashed(self.user.id, 'other-456')

    # A partial update of one field leaves the password alone
    def test_patch_single_field_keeps_password(self):
        old_password = self.user.password
        response = self.client.patch(self.detail_url, {'mobile': '555-0100'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNoPassword(response)
        self.user.refresh_from_db()
        self.assertEqual(self.user.mobile, '555-0100')
        self.assertEqual(self.user.password, old_password)

    # Anonymous clients cannot update a user
    def test_patch_requires_authentication(self):
        response = APIClient().patch(self.detail_url, {'mobile': '555-0100'}, format='json')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.user.refresh_from_db()
        self.assertIsNone(self.user.mobile)

    # The data migration hashes plain text and skips existing hashes
    def test_migration_hashes_only_plain_text(self):
        plain = User.objects.create(
            first_name='P', last_name='T', username='pt', email='pt@example.com',
            password='plain-text',
        )
        hashed_before = self.user.password
        hash_migration.hash_plain_text_passwords(apps, None)
        self.assertHashed(plain.id, 'plain-text')
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, hashed_before)

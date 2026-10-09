from django.contrib.auth.models import User as AuthUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Blog, User


class ModelStubRemovalTests(APITestCase):
    # The models expose the managers and exceptions Django generates (#13)
    def test_models_use_django_generated_attributes(self):
        for model in (User, Blog):
            with self.subTest(model=model.__name__):
                self.assertIsInstance(model.objects, models.Manager)
                self.assertTrue(issubclass(model.DoesNotExist, ObjectDoesNotExist))

    # Looking up a missing row raises the model's own DoesNotExist
    def test_missing_row_raises_does_not_exist(self):
        with self.assertRaises(Blog.DoesNotExist):
            Blog.objects.get(pk=999)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=999)

    # The detail views turn DoesNotExist into a 404
    def test_detail_views_return_404_for_missing_ids(self):
        self.client.force_authenticate(AuthUser.objects.create_user('reader'))
        for name, kwargs in (
            ('blog-detail', {'blog_id': 999}),
            ('user-detail', {'user_id': 999}),
            ('user-blogs', {'user_id': 999}),
        ):
            with self.subTest(url=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

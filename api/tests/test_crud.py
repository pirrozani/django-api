from django.contrib.auth.models import User as Account
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Blog, User
from api.tests.test_blog_ownership import make_author

NEW_AUTHOR = {
    'first_name': 'Ada',
    'last_name': 'Lovelace',
    'username': 'ada',
    'password': 'secret-123',
    'email': 'ada@example.com',
}


# Full create/read/update/delete round trips for authors and blogs (#14)
class CrudTests(APITestCase):
    # A staff account with its own author, so it may create, edit and delete both
    def setUp(self):
        self.account = Account.objects.create_user('admin', password='x', is_staff=True)
        make_author('admin', self.account)
        self.client.force_authenticate(self.account)

    # Authors: POST, GET, PUT, PATCH, DELETE, then GET is a 404 with a detail body
    def test_user_crud(self):
        response = self.client.post(reverse('user-list'), NEW_AUTHOR, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse('user-detail', args=[response.json()['id']])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['username'], 'ada')

        data = {k: v for k, v in NEW_AUTHOR.items() if k != 'password'}
        response = self.client.put(url, {**data, 'first_name': 'Augusta'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['first_name'], 'Augusta')

        response = self.client.patch(url, {'last_name': 'King'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['first_name'], 'Augusta')
        self.assertEqual(response.json()['last_name'], 'King')

        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(set(response.json()), {'detail'})

    # Blogs: POST, GET, PUT, PATCH, DELETE, then GET is a 404 with a detail body
    def test_blog_crud(self):
        data = {'title': 'First', 'content': 'Body'}
        response = self.client.post(reverse('blog-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse('blog-detail', args=[response.json()['id']])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'First')

        data = {'title': 'Second', 'content': 'New'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['content'], 'New')

        response = self.client.patch(url, {'title': 'Third'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['content'], 'New')

        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(set(response.json()), {'detail'})

    # Writes to a missing object are 404s with a detail body, not 500s
    def test_writes_to_missing_object_return_404(self):
        for name in ('user-detail', 'blog-detail'):
            for method in ('put', 'patch', 'delete'):
                with self.subTest(url=name, method=method):
                    url = reverse(name, args=[999])
                    response = getattr(self.client, method)(url, {}, format='json')
                    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                    self.assertEqual(set(response.json()), {'detail'})

    # Invalid input is a 400 with field errors
    def test_invalid_input_returns_400(self):
        response = self.client.post(reverse('blog-list'), {'title': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.json())


# Every write needs a login and changes nothing without one (#9, #14)
class AnonymousWriteTests(APITestCase):
    # One author with one blog; the client stays anonymous
    def setUp(self):
        self.author = make_author('alee')
        self.blog = Blog.objects.create(user=self.author, title='Hello', content='World')

    # Anonymous POST, PUT, PATCH and DELETE are 401s with a detail body
    def test_writes_return_401(self):
        user_url = reverse('user-detail', args=[self.author.id])
        blog_url = reverse('blog-detail', args=[self.blog.id])
        requests = [('post', reverse('user-list'), NEW_AUTHOR)]
        requests += [('post', reverse('blog-list'), {'title': 'X', 'content': 'Y'})]
        for method in ('put', 'patch', 'delete'):
            requests += [(method, user_url, {**NEW_AUTHOR, 'first_name': 'X'})]
            requests += [(method, blog_url, {'title': 'X', 'content': 'Y'})]
        for method, url, data in requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, data, format='json')
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertEqual(set(response.json()), {'detail'})

        self.author.refresh_from_db()
        self.blog.refresh_from_db()
        self.assertEqual(self.author.first_name, 'Ann')
        self.assertEqual(self.blog.title, 'Hello')
        self.assertEqual((User.objects.count(), Blog.objects.count()), (1, 1))

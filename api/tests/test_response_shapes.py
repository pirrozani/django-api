from django.contrib.auth.models import User as Account
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Blog, User

NEW_USER = {
    'first_name': 'Ada',
    'last_name': 'Lovelace',
    'username': 'ada',
    'password': 'secret-123',
    'email': 'ada@example.com',
}


class ResponseShapeTests(APITestCase):
    # Create an author with one blog and log the client in with an auth account
    def setUp(self):
        self.client.force_authenticate(Account.objects.create_user('demo', password='x'))
        self.user = User.objects.create(
            first_name='Ann', last_name='Lee', username='alee', email='ann@example.com',
            password='pbkdf2_sha256$1$salt$hash',
        )
        self.blog = Blog.objects.create(user=self.user, title='Hello', content='World')

    # POST returns 201 with the created object, not wrapped in a plural key
    def test_create_returns_unwrapped_object(self):
        response = self.client.post(reverse('user-list'), NEW_USER, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['email'], NEW_USER['email'])
        self.assertNotIn('Users', response.json())

        data = {'user': self.user.id, 'title': 'New', 'content': 'Body'}
        response = self.client.post(reverse('blog-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['title'], 'New')
        self.assertNotIn('Blogs', response.json())

    # Missing objects return DRF's default {"detail": ...} 404 body
    def test_404_uses_detail_key(self):
        for name in ('user-detail', 'blog-detail', 'user-blogs'):
            with self.subTest(url=name):
                response = self.client.get(reverse(name, args=[999]))
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                self.assertEqual(set(response.json()), {'detail'})

    # DELETE returns 204 with an empty body
    def test_delete_returns_empty_204(self):
        for name, pk in (('blog-detail', self.blog.id), ('user-detail', self.user.id)):
            with self.subTest(url=name):
                response = self.client.delete(reverse(name, args=[pk]))
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                self.assertEqual(response.content, b'')

    # Deleting a user also deletes their blogs
    def test_delete_user_cascades_blogs(self):
        response = self.client.delete(reverse('user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Blog.objects.filter(pk=self.blog.id).exists())

    # A user's blogs are listed; a user without blogs gets 200 and an empty list
    def test_user_blogs_lists_and_allows_empty(self):
        response = self.client.get(reverse('user-blogs', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([b['id'] for b in response.json()], [self.blog.id])

        empty = User.objects.create(
            first_name='No', last_name='Blogs', username='nb', email='nb@example.com',
            password='pbkdf2_sha256$1$salt$hash',
        )
        response = self.client.get(reverse('user-blogs', args=[empty.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    # PATCH on a blog changes only the fields sent
    def test_patch_blog_is_partial(self):
        response = self.client.patch(reverse('blog-detail', args=[self.blog.id]), {'title': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'X')
        self.assertEqual(response.json()['content'], 'World')

    # Anonymous writes are rejected; reads are public (#9)
    def test_anonymous_writes_are_rejected(self):
        self.client.force_authenticate(None)
        requests = (
            ('post', reverse('blog-list')),
            ('delete', reverse('blog-detail', args=[self.blog.id])),
            ('patch', reverse('user-detail', args=[self.user.id])),
        )
        for method, url in requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Every route ends with a slash and the old /api/blogs/user/<id> is gone
    def test_routes_use_trailing_slash(self):
        self.assertEqual(reverse('user-detail', args=[1]), '/api/users/1/')
        self.assertEqual(reverse('user-blogs', args=[1]), '/api/users/1/blogs/')
        self.assertEqual(reverse('blog-detail', args=[1]), '/api/blogs/1/')
        for url in (f'/api/blogs/user/{self.user.id}', '/api/', '/api/users.json'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

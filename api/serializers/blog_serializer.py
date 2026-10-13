from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from api.models.blog import Blog
from api.models.user import User


# The AuthorSummarySerializer class is a read-only summary of a blog's author
class AuthorSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = fields


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='Example response',
            summary='Detailed example',
            value={
                'id': 1,
                'user': 1,
                'author': {
                    'id': 1,
                    'username': 'lyang',
                    'first_name': 'Robert',
                    'last_name': 'Oliver',
                },
                'title': 'Doloremque et et.',
                'content': 'Discuss than some debate this. Entire him certain single west rock......',
                'created_at': '2021-06-11',
            },
            response_only=True,
        ),
        OpenApiExample(
            name='Example request',
            summary='Create or update a blog',
            value={
                'title': 'Doloremque et et.',
                'content': 'Discuss than some debate this. Entire him certain single west rock......',
            },
            request_only=True,
        ),
    ],
)
# The BlogSerializer class serializes Blog: `user` (id) and `author` (summary) are read-only,
# since the author comes from the caller's token
class BlogSerializer(serializers.ModelSerializer):
    author = AuthorSummarySerializer(source='user', read_only=True)

    class Meta:
        model = Blog
        fields = ['id', 'user', 'author', 'title', 'content', 'created_at']
        read_only_fields = ['user']

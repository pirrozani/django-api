from rest_framework import serializers
from api.models.blog import Blog
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='Example response',
            summary='Detailed example',
            value={
                'id': 1,
                'user_id': 1,
                'title': 'Doloremque et et.',
                'content': 'Discuss than some debate this. Entire him certain single west rock......',
                'created_at': '2021-06-11'
            }
        )
    ],
)
# The BlogSerializer class is used to serialize the Blog model
class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = '__all__'

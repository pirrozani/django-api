from rest_framework import serializers
from api.models.user import User
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.contrib.auth.hashers import make_password


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name='Example response',
            summary='Detailed example',
            value={
                'id': 1,
                'first_name': 'Robert',
                'last_name': 'Oliver',
                'username': 'lyang',
                'mobile': '(482)598-4678',
                'email': 'breanna03@example.com',
                }
        )
    ]
)
# The UserSerializer class is used to serialize the User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'mobile', 'password', 'email', 'register_at']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'), None, 'pbkdf2_sha256')
        return super(UserSerializer, self).create(validated_data)
    
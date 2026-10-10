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
                },
            response_only=True,
        )
    ]
)
# The UserSerializer class is used to serialize the User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'mobile', 'password', 'email', 'register_at']
        extra_kwargs = {'password': {'write_only': True}}

    # Hash the password before the user is stored
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    # Hash the password only when the update supplies one
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)


# The UserUpdateSerializer class is used for PUT/PATCH, where the password is optional
class UserUpdateSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

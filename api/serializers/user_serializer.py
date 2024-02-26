from rest_framework import serializers
from api.models.user import User
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


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
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserSerializer, self).__init__(*args, **kwargs)
        if 'context' in kwargs and kwargs['context'].get('request_method') == 'PUT':
            self.fields['first_name'].required = False
            self.fields['last_name'].required = False
            self.fields['email'].required = False
            self.fields['password'].required = False

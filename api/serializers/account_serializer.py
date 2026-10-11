from django.contrib.auth.models import User as Account
from rest_framework import serializers


# The AccountSerializer class describes the logged-in login account (auth.User, not api.User)
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'username', 'is_staff']
        read_only_fields = fields

from django.contrib.auth.models import User as Account
from rest_framework import serializers


# The AccountSerializer class describes the logged-in login account (auth.User, not api.User)
class AccountSerializer(serializers.ModelSerializer):
    # The author this account writes as; null when the account has no author profile
    author_id = serializers.IntegerField(
        source='author.id',
        read_only=True,
        allow_null=True,
        help_text='Id of the author this account writes as, or null if it has none.',
    )

    class Meta:
        model = Account
        fields = ['id', 'username', 'is_staff', 'author_id']
        read_only_fields = fields

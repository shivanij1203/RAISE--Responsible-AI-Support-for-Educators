from rest_framework import serializers
from django.contrib.auth.models import User


class UserRefSerializer(serializers.Serializer):
    """Compact user reference: display name + email.

    Display name falls back to email when first_name is empty.
    """

    name = serializers.SerializerMethodField()
    email = serializers.EmailField()

    def get_name(self, obj: User) -> str:
        return obj.first_name or obj.email

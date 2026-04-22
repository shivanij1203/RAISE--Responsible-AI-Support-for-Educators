from rest_framework import serializers


class CheckpointCommentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()
    userName = serializers.SerializerMethodField()
    userRole = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()

    def get_userName(self, obj) -> str:
        return obj.user.first_name or obj.user.email

    def get_userRole(self, obj) -> str:
        profile = getattr(obj.user, 'profile', None)
        return profile.role if profile else 'unknown'

    def get_createdAt(self, obj) -> str:
        return obj.created_at.isoformat()

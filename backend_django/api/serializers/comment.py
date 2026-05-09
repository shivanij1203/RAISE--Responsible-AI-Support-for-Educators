from rest_framework import serializers


class CheckpointCommentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()
    userName = serializers.SerializerMethodField()
    userRole = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()
    resolved = serializers.BooleanField()
    resolvedAt = serializers.SerializerMethodField()
    resolvedBy = serializers.SerializerMethodField()

    def get_userName(self, obj) -> str:
        return obj.user.first_name or obj.user.email

    def get_userRole(self, obj) -> str:
        profile = getattr(obj.user, 'profile', None)
        return profile.role if profile else 'unknown'

    def get_createdAt(self, obj) -> str:
        return obj.created_at.isoformat()

    def get_resolvedAt(self, obj) -> str | None:
        return obj.resolved_at.isoformat() if obj.resolved_at else None

    def get_resolvedBy(self, obj) -> str | None:
        if not obj.resolved_by:
            return None
        return obj.resolved_by.first_name or obj.resolved_by.email

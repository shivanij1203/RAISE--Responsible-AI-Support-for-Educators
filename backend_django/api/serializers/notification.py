from rest_framework import serializers


class NotificationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    verb = serializers.CharField()
    message = serializers.CharField()
    read = serializers.BooleanField()
    createdAt = serializers.SerializerMethodField()
    projectId = serializers.SerializerMethodField()
    checkpointId = serializers.SerializerMethodField()
    actorName = serializers.SerializerMethodField()

    def get_createdAt(self, obj) -> str:
        return obj.created_at.isoformat()

    def get_projectId(self, obj) -> int | None:
        return obj.project_id

    def get_checkpointId(self, obj) -> str | None:
        return obj.checkpoint.checkpoint_id if obj.checkpoint else None

    def get_actorName(self, obj) -> str:
        if not obj.actor:
            return 'Someone'
        return obj.actor.first_name or obj.actor.email

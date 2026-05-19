from rest_framework import serializers


class ActivityEventSerializer(serializers.Serializer):
    """Serializes an ActivityEvent for the activity timeline view."""

    id = serializers.IntegerField()
    eventType = serializers.CharField(source='event_type')
    summary = serializers.CharField()
    actorName = serializers.SerializerMethodField()
    checkpointId = serializers.SerializerMethodField()
    checkpointLabel = serializers.SerializerMethodField()
    metadata = serializers.JSONField()
    createdAt = serializers.SerializerMethodField()

    def get_actorName(self, obj) -> str | None:
        if obj.actor is None:
            return None
        return obj.actor.first_name or obj.actor.email or obj.actor.username

    def get_checkpointId(self, obj) -> str | None:
        return obj.checkpoint.checkpoint_id if obj.checkpoint else None

    def get_checkpointLabel(self, obj) -> str | None:
        return obj.checkpoint.label if obj.checkpoint else None

    def get_createdAt(self, obj) -> str:
        return obj.created_at.isoformat()

from rest_framework import serializers


class InvitationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    role = serializers.CharField()
    status = serializers.CharField()
    note = serializers.CharField(allow_blank=True)
    toEmail = serializers.SerializerMethodField()
    fromName = serializers.SerializerMethodField()
    fromEmail = serializers.SerializerMethodField()
    projectId = serializers.SerializerMethodField()
    projectName = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()
    respondedAt = serializers.SerializerMethodField()

    def get_toEmail(self, obj) -> str:
        return obj.to_email

    def get_fromName(self, obj) -> str:
        u = obj.from_user
        return u.first_name or u.username

    def get_fromEmail(self, obj) -> str:
        return obj.from_user.email

    def get_projectId(self, obj) -> int:
        return obj.project_id

    def get_projectName(self, obj) -> str:
        return obj.project.name

    def get_createdAt(self, obj) -> str:
        return obj.created_at.isoformat()

    def get_respondedAt(self, obj) -> str | None:
        return obj.responded_at.isoformat() if obj.responded_at else None

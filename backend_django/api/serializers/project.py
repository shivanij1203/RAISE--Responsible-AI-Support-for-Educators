from rest_framework import serializers

from api.serializers.user import UserRefSerializer


_STUDENT_DATA_CHECKPOINTS = {'data_deidentified', 'data_storage', 'ferpa_compliance'}
_EXTERNAL_SERVICE_CHECKPOINTS = {'data_storage', 'data_deidentified'}
_DECISION_CHECKPOINTS = {'bias_audit', 'human_review', 'grading_fairness', 'admin_bias_audit'}
_HUMAN_SUBJECTS_CHECKPOINTS = {'irb', 'participant_consent'}


def infer_risk_context(checkpoint_ids: set[str]) -> dict[str, bool]:
    """Infer risk context from the checkpoint IDs that exist on a project."""
    return {
        'involves_student_data': bool(checkpoint_ids & _STUDENT_DATA_CHECKPOINTS),
        'data_leaves_institution': bool(checkpoint_ids & _EXTERNAL_SERVICE_CHECKPOINTS),
        'affects_decisions': bool(checkpoint_ids & _DECISION_CHECKPOINTS),
        'involves_human_subjects': bool(checkpoint_ids & _HUMAN_SUBJECTS_CHECKPOINTS),
    }


class CheckpointSerializer(serializers.Serializer):
    id = serializers.CharField(source='checkpoint_id')
    dbId = serializers.IntegerField(source='id')
    label = serializers.CharField()
    category = serializers.CharField()
    assignedTo = serializers.CharField(source='assigned_to')
    completed = serializers.BooleanField()
    completedAt = serializers.SerializerMethodField()
    what = serializers.CharField()
    why = serializers.CharField()
    how = serializers.CharField()
    frameworks = serializers.JSONField()
    commentCount = serializers.SerializerMethodField()
    unresolvedCommentCount = serializers.SerializerMethodField()

    def get_completedAt(self, obj) -> str | None:
        return obj.completed_at.isoformat() if obj.completed_at else None

    def get_commentCount(self, obj) -> int:
        return obj.comments.count()

    def get_unresolvedCommentCount(self, obj) -> int:
        return obj.comments.filter(resolved=False).count()


class DecisionSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    checkpoint = serializers.CharField(source='checkpoint.checkpoint_id')
    description = serializers.CharField()
    notes = serializers.CharField()
    proofType = serializers.SerializerMethodField()
    proofValue = serializers.SerializerMethodField()
    toolUsed = serializers.SerializerMethodField()
    loggedAt = serializers.SerializerMethodField()

    def get_id(self, obj) -> str:
        return str(obj.id)

    def get_proofType(self, obj) -> str | None:
        return obj.proof_type or None

    def get_proofValue(self, obj) -> str | None:
        return obj.proof_value or None

    def get_toolUsed(self, obj) -> dict | None:
        if not obj.tool_used:
            return None
        return {'id': obj.tool_used.id, 'name': obj.tool_used.name}

    def get_loggedAt(self, obj) -> str:
        return obj.logged_at.isoformat()


class _AIToolRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()
    category = serializers.CharField()


class ProjectSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    name = serializers.CharField()
    description = serializers.CharField()
    aiUseCase = serializers.CharField(source='ai_use_case')
    category = serializers.CharField(allow_null=True, allow_blank=True)
    status = serializers.CharField()
    createdAt = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    ownerEmail = serializers.EmailField(source='user.email')
    facultyAdvisor = UserRefSerializer(source='faculty_advisor', allow_null=True)
    studentCollaborator = UserRefSerializer(source='student_collaborator', allow_null=True)
    checkpoints = serializers.SerializerMethodField()
    decisions = serializers.SerializerMethodField()
    aiTools = _AIToolRefSerializer(source='ai_tools', many=True)
    riskContext = serializers.SerializerMethodField()
    shareAsExample = serializers.BooleanField(source='share_as_example')

    def get_id(self, obj) -> str:
        return str(obj.id)

    def get_createdAt(self, obj) -> str:
        return obj.created_at.isoformat()

    def get_owner(self, obj) -> str:
        return obj.user.first_name or obj.user.email

    def get_checkpoints(self, obj) -> list[dict]:
        return CheckpointSerializer(obj.checkpoints.order_by('id'), many=True).data

    def get_decisions(self, obj) -> list[dict]:
        qs = obj.decisions.select_related('tool_used').order_by('-logged_at')
        return DecisionSerializer(qs, many=True).data

    def get_riskContext(self, obj) -> dict[str, bool]:
        ids = set(obj.checkpoints.values_list('checkpoint_id', flat=True))
        return infer_risk_context(ids)


class CheckpointToggleResponseSerializer(serializers.Serializer):
    id = serializers.CharField(source='checkpoint_id')
    completed = serializers.BooleanField()
    completedAt = serializers.SerializerMethodField()

    def get_completedAt(self, obj) -> str | None:
        return obj.completed_at.isoformat() if obj.completed_at else None


class DecisionCreateResponseSerializer(DecisionSerializer):
    """DecisionSerializer plus the auto-complete status of the checkpoint."""

    checkpointCompleted = serializers.SerializerMethodField()
    checkpointCompletedAt = serializers.SerializerMethodField()

    def get_checkpointCompleted(self, obj) -> bool:
        return obj.checkpoint.completed

    def get_checkpointCompletedAt(self, obj) -> str | None:
        cp = obj.checkpoint
        return cp.completed_at.isoformat() if cp.completed_at else None

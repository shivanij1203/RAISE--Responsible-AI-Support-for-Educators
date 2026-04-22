from rest_framework import serializers


class AIToolSerializer(serializers.Serializer):
    """Full AI tool serializer. Pass context={'include_guidance': True} to
    include the per-use-case compliance guidance payload.
    """

    id = serializers.IntegerField()
    toolType = serializers.CharField(source='tool_type')
    toolTypeDisplay = serializers.SerializerMethodField()
    name = serializers.CharField()
    description = serializers.CharField()
    vendor = serializers.CharField()
    category = serializers.CharField()
    categoryDisplay = serializers.SerializerMethodField()
    status = serializers.CharField()
    statusDisplay = serializers.SerializerMethodField()
    riskNotes = serializers.CharField(source='risk_notes')
    websiteUrl = serializers.CharField(source='website_url')
    addedBy = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()
    projectCount = serializers.SerializerMethodField()
    retainsData = serializers.CharField(source='retains_data')
    dataRetentionDetails = serializers.CharField(source='data_retention_details')
    sendsToThirdParty = serializers.BooleanField(source='sends_to_third_party')
    hipaaCompliant = serializers.BooleanField(source='hipaa_compliant')
    ferpaCompliant = serializers.BooleanField(source='ferpa_compliant')
    hasEnterprisePlan = serializers.BooleanField(source='has_enterprise_plan')
    recommendedUseCases = serializers.JSONField(source='recommended_use_cases')
    complianceGuidance = serializers.SerializerMethodField()

    def get_toolTypeDisplay(self, obj) -> str:
        return obj.get_tool_type_display()

    def get_categoryDisplay(self, obj) -> str:
        return obj.get_category_display()

    def get_statusDisplay(self, obj) -> str:
        return obj.get_status_display()

    def get_addedBy(self, obj) -> str | None:
        if not obj.added_by:
            return None
        return obj.added_by.first_name or obj.added_by.email

    def get_createdAt(self, obj) -> str:
        return obj.created_at.isoformat()

    def get_projectCount(self, obj) -> int:
        return obj.projects.count()

    def get_complianceGuidance(self, obj) -> dict | None:
        if not self.context.get('include_guidance'):
            return None
        return obj.compliance_guidance or {}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get('include_guidance'):
            data.pop('complianceGuidance', None)
        return data

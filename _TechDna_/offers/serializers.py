from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.serializers import UserPublicSerializer
from assessments.models import Assessment

from .models import JobOffer

User = get_user_model()


class AssessmentBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ["id", "title", "slug"]


class JobOfferSerializer(serializers.ModelSerializer):
    """Representación de lectura. Las escrituras van por los Input serializers."""

    assessment = AssessmentBriefSerializer(read_only=True)
    evaluator = UserPublicSerializer(read_only=True)
    candidate = UserPublicSerializer(read_only=True)
    created_by = UserPublicSerializer(read_only=True)
    awaiting = UserPublicSerializer(source="awaiting_user", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    modality_display = serializers.CharField(source="get_modality_display", read_only=True)
    can_respond = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = JobOffer
        fields = [
            "id",
            "assessment",
            "evaluator",
            "candidate",
            "created_by",
            "awaiting",
            "parent",
            "position_title",
            "salary",
            "modality",
            "modality_display",
            "message",
            "status",
            "status_display",
            "expires_at",
            "responded_at",
            "created_at",
            "updated_at",
            "can_respond",
            "can_cancel",
        ]
        read_only_fields = fields

    def _user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_can_respond(self, obj) -> bool:
        user = self._user()
        return bool(user and user.is_authenticated and obj.can_respond(user))

    def get_can_cancel(self, obj) -> bool:
        user = self._user()
        return bool(user and user.is_authenticated and obj.can_cancel(user))


class CreateJobOfferInputSerializer(serializers.Serializer):
    assessment = serializers.PrimaryKeyRelatedField(queryset=Assessment.objects.all())
    candidate = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    position_title = serializers.CharField(max_length=150)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    modality = serializers.ChoiceField(
        choices=JobOffer.Modality.choices,
        default=JobOffer.Modality.REMOTE,
    )
    message = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class CounterJobOfferInputSerializer(serializers.Serializer):
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    modality = serializers.ChoiceField(choices=JobOffer.Modality.choices, required=False)
    message = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

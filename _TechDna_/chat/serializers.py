from rest_framework import serializers

from assessments.models import Assessment

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_username",
            "text",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "conversation", "sender", "is_read", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    buyer_username = serializers.CharField(source="buyer.username", read_only=True)
    seller_username = serializers.CharField(source="seller.username", read_only=True)
    assessment_title = serializers.CharField(
        source="assessment.title",
        read_only=True,
    )
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "assessment",
            "assessment_title",
            "buyer",
            "buyer_username",
            "seller",
            "seller_username",
            "created_at",
            "updated_at",
            "last_message",
            "unread_count",
        ]
        read_only_fields = fields

    def get_last_message(self, obj):
        last = obj.messages.last()
        return last.text if last else None

    def get_unread_count(self, obj):
        user = self.context["request"].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


class SendMessageInputSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=1000)


class StartConversationInputSerializer(serializers.Serializer):
    assessment_id = serializers.PrimaryKeyRelatedField(
        queryset=Assessment.objects.all(),
        source="assessment",
    )

    def validate_assessment(self, assessment):
        if not assessment.active:
            raise serializers.ValidationError(
                "No se puede iniciar una conversación sobre esta evaluación."
            )
        return assessment

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation
from .permissions import IsConversationParticipant
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    SendMessageInputSerializer,
    StartConversationInputSerializer,
)
from .services import (
    get_or_create_conversation,
    mark_messages_as_read,
    send_message,
)


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def get_queryset(self):
        user = self.request.user
        return (
            Conversation.objects.filter(Q(buyer=user) | Q(seller=user))
            .select_related("assessment", "buyer", "seller")
            .prefetch_related("messages")
        )

    @action(detail=False, methods=["post"])
    def start(self, request):
        serializer = StartConversationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            conversation = get_or_create_conversation(
                buyer=request.user,
                assessment_id=serializer.validated_data["assessment"].pk,
            )
        except ValidationError as error:
            return Response(
                {"detail": error.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.get_serializer(conversation).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        mark_messages_as_read(conversation_id=conversation.pk, user=request.user)
        messages_qs = conversation.messages.select_related("sender").all()
        return Response(MessageSerializer(messages_qs, many=True).data)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        conversation = self.get_object()
        serializer = SendMessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            message = send_message(
                user=request.user,
                conversation_id=conversation.pk,
                text=serializer.validated_data["text"],
            )
        except PermissionDenied as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValidationError as error:
            return Response(
                {"detail": error.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )
from rest_framework.permissions import BasePermission

from .models import Conversation, Message


class IsConversationParticipant(BasePermission):
    """Permite el acceso solo si el usuario es el estudiante o el instructor de la conversación."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Message):
            conversation = obj.conversation
        elif isinstance(obj, Conversation):
            conversation = obj
        else:
            return False

        return request.user in (conversation.student, conversation.instructor)

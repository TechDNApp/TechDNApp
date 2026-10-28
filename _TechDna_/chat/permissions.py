from rest_framework.permissions import BasePermission

from .models import Conversation, Message


class IsConversationParticipant(BasePermission):
    """Allow access only to users participating in the conversation."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Message):
            conversation = obj.conversation
        elif isinstance(obj, Conversation):
            conversation = obj
        else:
            return False

        return request.user in (conversation.buyer, conversation.seller)

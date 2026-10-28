from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from assessments.models import Assessment
from .models import Conversation, Message


@transaction.atomic
def get_or_create_conversation(buyer, assessment_id):
    """
    Obtiene o inicia una conversación entre un usuario y el dueño de una evaluación.
    Bloquea la fila de la evaluación para asegurar consistencia.
    """
    assessment = Assessment.objects.select_for_update().get(pk=assessment_id)
    if assessment.owner == buyer:
        raise ValidationError(
            "No puedes iniciar una conversación sobre tu propia evaluación."
        )
    if not assessment.active:
        raise ValidationError(
            "No se puede iniciar una conversación sobre esta evaluación."
        )
    conversation, _ = Conversation.objects.get_or_create(
        assessment=assessment,
        buyer=buyer,
        defaults={"seller": assessment.owner},
    )
    return conversation


@transaction.atomic
def send_message(user, conversation_id, text):
    """
    Envía un mensaje validando que el remitente sea participante de la conversación.
    """
    clean_text = text.strip()
    if not clean_text:
        raise ValidationError("El mensaje no puede estar vacío.")
    conversation = Conversation.objects.select_for_update().get(pk=conversation_id)
    if user != conversation.buyer and user != conversation.seller:
        raise PermissionDenied(
            "No tienes permiso para enviar mensajes en esta conversación."
        )
    message = Message.objects.create(
        conversation=conversation,
        sender=user,
        text=clean_text,
    )
    # Actualiza la marca de tiempo de la conversación para ordenación en bandeja de entrada
    conversation.save(update_fields=["updated_at"])
    return message


@transaction.atomic
def mark_messages_as_read(conversation_id, user):
    """
    Marca como leídos los mensajes recibidos pendientes.
    """
    conversation = Conversation.objects.get(pk=conversation_id)
    if user != conversation.buyer and user != conversation.seller:
        raise PermissionDenied("No tienes acceso a esta conversación.")
    Message.objects.filter(
        conversation=conversation,
        is_read=False,
    ).exclude(
        sender=user
    ).update(is_read=True)

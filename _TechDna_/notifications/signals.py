from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.models import Message
from .models import NotificationType
from .tasks import create_notification_async

@receiver(post_save, sender=Message)
def notify_new_chat_message(sender, instance, created, **kwargs):
    if created:
        conv = instance.conversation
        # Determine the recipient (if sender is buyer, recipient is seller/profesor, and vice versa)
        recipient = conv.seller if instance.sender == conv.buyer else conv.buyer
        
        create_notification_async.delay(
            recipient_id=recipient.pk,
            notification_type=NotificationType.NEW_MESSAGE,
            title="Nuevo mensaje en evaluación",
            body=f"{instance.sender.username}: {instance.text[:50]}...",
            link=f"/api/v1/conversations/{conv.pk}/",
        )
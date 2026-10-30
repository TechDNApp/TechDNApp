from celery import shared_task
from .models import Notification, NotificationType

@shared_task
def create_notification_async(recipient_id, notification_type, title, body, link=""):
    """
    Creates a notification asynchronously using Celery.
    """
    Notification.objects.create(
        recipient_id=recipient_id,
        notification_type=notification_type,
        title=title,
        body=body,
        link=link,
    )
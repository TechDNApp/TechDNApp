from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from assessments.models import Assessment
from skills.models import Category, Role, Technology

from .models import Conversation
from .services import (
    get_or_create_conversation,
    mark_messages_as_read,
    send_message,
)


class ChatTestDataMixin:
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="owner")
        self.buyer = user_model.objects.create_user(username="buyer")
        self.other_user = user_model.objects.create_user(username="other")

        category = Category.objects.create(name="Programming")
        technology = Technology.objects.create(
            category=category,
            name="Python",
        )
        role = Role.objects.create(name="Backend Developer")
        self.assessment = Assessment.objects.create(
            owner=self.owner,
            title="Python Backend",
            description="Assessment description",
            technology=technology,
            role=role,
        )


class ChatServiceTests(ChatTestDataMixin, TestCase):
    def test_get_or_create_conversation_uses_assessment_owner(self):
        conversation = get_or_create_conversation(self.buyer, self.assessment.pk)
        same_conversation = get_or_create_conversation(self.buyer, self.assessment.pk)

        self.assertEqual(conversation, same_conversation)
        self.assertEqual(conversation.assessment, self.assessment)
        self.assertEqual(conversation.seller, self.owner)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_cannot_start_conversation_with_own_assessment(self):
        with self.assertRaises(ValidationError):
            get_or_create_conversation(self.owner, self.assessment.pk)

    def test_cannot_start_conversation_for_inactive_assessment(self):
        self.assessment.active = False
        self.assessment.save(update_fields=["active"])

        with self.assertRaises(ValidationError):
            get_or_create_conversation(self.buyer, self.assessment.pk)

    def test_only_participants_can_send_and_read_messages(self):
        conversation = get_or_create_conversation(self.buyer, self.assessment.pk)
        message = send_message(self.buyer, conversation.pk, "  Hola  ")

        self.assertEqual(message.text, "Hola")
        with self.assertRaises(PermissionDenied):
            send_message(self.other_user, conversation.pk, "No autorizado")
        with self.assertRaises(PermissionDenied):
            mark_messages_as_read(conversation.pk, self.other_user)

        mark_messages_as_read(conversation.pk, self.owner)
        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_cannot_send_empty_message(self):
        conversation = get_or_create_conversation(self.buyer, self.assessment.pk)

        with self.assertRaises(ValidationError):
            send_message(self.buyer, conversation.pk, "  ")


class ChatAPITests(ChatTestDataMixin, APITestCase):
    def test_authenticated_user_can_start_conversation_and_send_message(self):
        self.client.force_authenticate(user=self.buyer)

        response = self.client.post(
            reverse("conversation-start"),
            {"assessment_id": self.assessment.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["assessment"], self.assessment.pk)
        self.assertEqual(response.data["seller"], self.owner.pk)
        conversation_id = response.data["id"]

        response = self.client.post(
            reverse("conversation-send", kwargs={"pk": conversation_id}),
            {"text": "Hola"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "Hola")
        self.assertEqual(response.data["sender"], self.buyer.pk)

    def test_user_can_only_list_own_conversations(self):
        own_conversation = get_or_create_conversation(
            self.buyer,
            self.assessment.pk,
        )
        other_assessment = Assessment.objects.create(
            owner=self.other_user,
            title="Other assessment",
            description="Another assessment",
            technology=self.assessment.technology,
            role=self.assessment.role,
        )
        get_or_create_conversation(self.owner, other_assessment.pk)
        self.client.force_authenticate(user=self.buyer)

        response = self.client.get(reverse("conversation-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], own_conversation.pk)

    def test_nonparticipant_cannot_access_conversation_messages(self):
        conversation = get_or_create_conversation(self.buyer, self.assessment.pk)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            reverse("conversation-messages", kwargs={"pk": conversation.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_start_conversation(self):
        response = self.client.post(
            reverse("conversation-start"),
            {"assessment_id": self.assessment.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_start_conversation_with_own_assessment(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(
            reverse("conversation-start"),
            {"assessment_id": self.assessment.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_start_conversation_for_inactive_assessment(self):
        self.assessment.active = False
        self.assessment.save(update_fields=["active"])
        self.client.force_authenticate(user=self.buyer)

        response = self.client.post(
            reverse("conversation-start"),
            {"assessment_id": self.assessment.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_opening_messages_marks_received_messages_as_read(self):
        conversation = get_or_create_conversation(self.buyer, self.assessment.pk)
        message = send_message(self.owner, conversation.pk, "Mensaje recibido")
        self.client.force_authenticate(user=self.buyer)

        response = self.client.get(
            reverse("conversation-messages", kwargs={"pk": conversation.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "Mensaje recibido")
        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_send_message_rejects_empty_text(self):
        conversation = get_or_create_conversation(self.buyer, self.assessment.pk)
        self.client.force_authenticate(user=self.buyer)

        response = self.client.post(
            reverse("conversation-send", kwargs={"pk": conversation.pk}),
            {"text": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

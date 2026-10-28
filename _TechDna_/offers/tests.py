from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from assessments.models import Assessment
from skills.models import Category, Role, Technology

from . import services
from .models import JobOffer


class OfferFixturesMixin:
    """Datos comunes: un evaluador con una evaluación y dos candidatos."""

    def setUp(self):
        self.evaluator = User.objects.create_user(
            username="evaluator", email="ev@example.com", password="pass12345",
            role="evaluator",
        )
        self.candidate = User.objects.create_user(
            username="candidate", email="ca@example.com", password="pass12345",
        )
        self.outsider = User.objects.create_user(
            username="outsider", email="out@example.com", password="pass12345",
        )
        category = Category.objects.create(name="Programación")
        self.assessment = Assessment.objects.create(
            title="Python Backend Junior",
            description="Prueba de backend",
            role=Role.objects.create(name="Backend Developer"),
            technology=Technology.objects.create(name="Python", category=category),
            owner=self.evaluator,
        )

    def make_offer(self, **overrides):
        data = {
            "evaluator": self.evaluator,
            "assessment_id": self.assessment.pk,
            "candidate_id": self.candidate.pk,
            "position_title": "Backend Developer Junior",
            "salary": Decimal("28000"),
            "modality": JobOffer.Modality.REMOTE,
        }
        data.update(overrides)
        return services.create_offer(**data)


# ----------------------------------------------------------------------
# Servicios (lógica de negocio)
# ----------------------------------------------------------------------

class CreateOfferServiceTests(OfferFixturesMixin, TestCase):

    def test_owner_can_create_offer(self):
        offer = self.make_offer()
        self.assertEqual(offer.status, JobOffer.Status.PENDING)
        self.assertEqual(offer.created_by, self.evaluator)
        self.assertEqual(offer.awaiting_user, self.candidate)

    def test_non_owner_cannot_create_offer(self):
        with self.assertRaises(PermissionDenied):
            self.make_offer(evaluator=self.outsider)

    def test_cannot_offer_to_self(self):
        with self.assertRaises(ValidationError):
            self.make_offer(candidate_id=self.evaluator.pk)

    def test_recipient_must_be_candidate(self):
        self.candidate.role = "evaluator"
        self.candidate.save()
        with self.assertRaises(ValidationError):
            self.make_offer()

    def test_inactive_assessment_rejected(self):
        self.assessment.active = False
        self.assessment.save()
        with self.assertRaises(ValidationError):
            self.make_offer()

    def test_salary_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self.make_offer(salary=0)

    def test_expiration_must_be_future(self):
        with self.assertRaises(ValidationError):
            self.make_offer(expires_at=timezone.now() - timedelta(minutes=1))

    def test_only_one_pending_offer_per_assessment_and_candidate(self):
        self.make_offer()
        with self.assertRaises(ValidationError):
            self.make_offer()
        self.assertEqual(JobOffer.objects.count(), 1)

    def test_new_offer_allowed_after_previous_is_closed(self):
        first = self.make_offer()
        services.reject_offer(self.candidate, first.pk)
        second = self.make_offer()
        self.assertEqual(second.status, JobOffer.Status.PENDING)


class TransitionServiceTests(OfferFixturesMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.offer = self.make_offer()

    def test_candidate_accepts(self):
        offer = services.accept_offer(self.candidate, self.offer.pk)
        self.assertEqual(offer.status, JobOffer.Status.ACCEPTED)
        self.assertIsNotNone(offer.responded_at)

    def test_author_cannot_accept_own_offer(self):
        with self.assertRaises(PermissionDenied):
            services.accept_offer(self.evaluator, self.offer.pk)

    def test_outsider_cannot_accept(self):
        with self.assertRaises(PermissionDenied):
            services.accept_offer(self.outsider, self.offer.pk)

    def test_candidate_rejects(self):
        offer = services.reject_offer(self.candidate, self.offer.pk)
        self.assertEqual(offer.status, JobOffer.Status.REJECTED)

    def test_author_cancels(self):
        offer = services.cancel_offer(self.evaluator, self.offer.pk)
        self.assertEqual(offer.status, JobOffer.Status.CANCELLED)

    def test_recipient_cannot_cancel(self):
        with self.assertRaises(PermissionDenied):
            services.cancel_offer(self.candidate, self.offer.pk)

    def test_closed_offer_cannot_change(self):
        services.accept_offer(self.candidate, self.offer.pk)
        with self.assertRaises(ValidationError):
            services.reject_offer(self.candidate, self.offer.pk)
        with self.assertRaises(ValidationError):
            services.cancel_offer(self.evaluator, self.offer.pk)

    def test_expired_offer_is_marked_and_cannot_be_accepted(self):
        JobOffer.objects.filter(pk=self.offer.pk).update(
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        with self.assertRaises(ValidationError):
            services.accept_offer(self.candidate, self.offer.pk)
        # El cambio a EXPIRED sobrevive al rollback de la transición fallida.
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, JobOffer.Status.EXPIRED)

    def test_expire_pending_offers(self):
        JobOffer.objects.filter(pk=self.offer.pk).update(
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertEqual(services.expire_pending_offers(), 1)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, JobOffer.Status.EXPIRED)


class CounterOfferServiceTests(OfferFixturesMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.offer = self.make_offer()

    def test_candidate_counters_then_evaluator_must_answer(self):
        counter = services.counter_offer(
            self.candidate, self.offer.pk, salary=Decimal("32000"),
        )
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, JobOffer.Status.COUNTERED)
        self.assertEqual(counter.parent, self.offer)
        self.assertEqual(counter.created_by, self.candidate)
        self.assertEqual(counter.awaiting_user, self.evaluator)

        # El autor de la contraoferta NO puede aceptarla...
        with self.assertRaises(PermissionDenied):
            services.accept_offer(self.candidate, counter.pk)
        # ...pero el evaluador sí.
        accepted = services.accept_offer(self.evaluator, counter.pk)
        self.assertEqual(accepted.status, JobOffer.Status.ACCEPTED)

    def test_ping_pong_negotiation_keeps_history(self):
        c1 = services.counter_offer(self.candidate, self.offer.pk, salary=Decimal("35000"))
        c2 = services.counter_offer(self.evaluator, c1.pk, salary=Decimal("31000"))
        services.accept_offer(self.candidate, c2.pk)

        history = services.get_negotiation_history(c2)
        self.assertEqual([o.pk for o in history], [self.offer.pk, c1.pk, c2.pk])
        self.assertEqual(
            JobOffer.objects.filter(status=JobOffer.Status.PENDING).count(), 0,
        )

    def test_author_cannot_counter_own_offer(self):
        with self.assertRaises(PermissionDenied):
            services.counter_offer(self.evaluator, self.offer.pk, salary=Decimal("30000"))

    def test_counter_must_change_terms(self):
        with self.assertRaises(ValidationError):
            services.counter_offer(self.candidate, self.offer.pk, salary=self.offer.salary)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, JobOffer.Status.PENDING)

    def test_counter_can_change_only_modality(self):
        counter = services.counter_offer(
            self.candidate, self.offer.pk,
            salary=self.offer.salary, modality=JobOffer.Modality.HYBRID,
        )
        self.assertEqual(counter.modality, JobOffer.Modality.HYBRID)


# ----------------------------------------------------------------------
# API REST
# ----------------------------------------------------------------------

class JobOfferAPITests(OfferFixturesMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.list_url = reverse("offer-list")

    def action_url(self, offer, name):
        return reverse(f"offer-{name}", kwargs={"pk": offer.pk})

    def test_requires_authentication(self):
        response = self.client.get(self.list_url)
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_create_offer(self):
        self.client.force_authenticate(self.evaluator)
        response = self.client.post(self.list_url, {
            "assessment": self.assessment.pk,
            "candidate": self.candidate.pk,
            "position_title": "Backend Junior",
            "salary": "27000.00",
            "modality": "hybrid",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["awaiting"]["id"], self.candidate.pk)

    def test_create_offer_not_owner_forbidden(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.post(self.list_url, {
            "assessment": self.assessment.pk,
            "candidate": self.candidate.pk,
            "position_title": "Backend Junior",
            "salary": "27000.00",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_offer_unknown_assessment_is_400_not_500(self):
        self.client.force_authenticate(self.evaluator)
        response = self.client.post(self.list_url, {
            "assessment": 99999,
            "candidate": self.candidate.pk,
            "position_title": "Backend Junior",
            "salary": "27000.00",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_own_offers_and_box_filter(self):
        self.make_offer()
        self.client.force_authenticate(self.candidate)
        self.assertEqual(self.client.get(self.list_url).data["count"], 1)
        self.assertEqual(self.client.get(self.list_url, {"box": "received"}).data["count"], 1)
        self.assertEqual(self.client.get(self.list_url, {"box": "sent"}).data["count"], 0)

        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get(self.list_url).data["count"], 0)

    def test_outsider_gets_404_on_actions(self):
        offer = self.make_offer()
        self.client.force_authenticate(self.outsider)
        for name in ("detail", "accept", "reject", "cancel"):
            method = self.client.get if name == "detail" else self.client.post
            response = method(self.action_url(offer, name))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, name)

    def test_unknown_offer_is_404(self):
        self.client.force_authenticate(self.candidate)
        response = self.client.post(reverse("offer-accept", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_by_candidate(self):
        offer = self.make_offer()
        self.client.force_authenticate(self.candidate)
        response = self.client.post(self.action_url(offer, "accept"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "accepted")

    def test_accept_by_author_is_403(self):
        offer = self.make_offer()
        self.client.force_authenticate(self.evaluator)
        response = self.client.post(self.action_url(offer, "accept"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_double_accept_is_400(self):
        offer = self.make_offer()
        self.client.force_authenticate(self.candidate)
        self.client.post(self.action_url(offer, "accept"))
        response = self.client.post(self.action_url(offer, "accept"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_counter_and_history(self):
        offer = self.make_offer()
        self.client.force_authenticate(self.candidate)
        response = self.client.post(self.action_url(offer, "counter"), {"salary": "33000"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        counter_id = response.data["id"]
        self.assertEqual(response.data["parent"], offer.pk)
        self.assertFalse(response.data["can_respond"])
        self.assertTrue(response.data["can_cancel"])

        self.client.force_authenticate(self.evaluator)
        response = self.client.get(reverse("offer-history", kwargs={"pk": counter_id}))
        self.assertEqual([o["id"] for o in response.data], [offer.pk, counter_id])

    def test_cancel_by_author(self):
        offer = self.make_offer()
        self.client.force_authenticate(self.evaluator)
        response = self.client.post(self.action_url(offer, "cancel"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")


# ----------------------------------------------------------------------
# Interfaz web
# ----------------------------------------------------------------------

class JobOfferWebTests(OfferFixturesMixin, TestCase):

    def test_list_requires_login(self):
        response = self.client.get(reverse("offers:list"))
        self.assertEqual(response.status_code, 302)

    def test_create_offer_from_form(self):
        self.client.force_login(self.evaluator)
        response = self.client.post(reverse("offers:create"), {
            "assessment": self.assessment.pk,
            "candidate": self.candidate.pk,
            "position_title": "Backend Junior",
            "salary": "26000",
            "modality": "remote",
            "message": "¡Enhorabuena por tu resultado!",
        })
        offer = JobOffer.objects.get()
        self.assertRedirects(response, offer.get_absolute_url())

    def test_create_form_only_lists_own_assessments(self):
        Assessment.objects.create(
            title="Otra evaluación", description="x",
            role=self.assessment.role, technology=self.assessment.technology,
            owner=self.outsider,
        )
        self.client.force_login(self.evaluator)
        response = self.client.get(reverse("offers:create"))
        queryset = response.context["form"].fields["assessment"].queryset
        self.assertEqual(list(queryset), [self.assessment])

    def test_received_tab_shows_pending_offer(self):
        self.make_offer()
        self.client.force_login(self.candidate)
        response = self.client.get(reverse("offers:list"), {"tab": "received"})
        self.assertContains(response, "Backend Developer Junior")

    def test_detail_hidden_from_outsider(self):
        offer = self.make_offer()
        self.client.force_login(self.outsider)
        response = self.client.get(offer.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_accept_via_post(self):
        offer = self.make_offer()
        self.client.force_login(self.candidate)
        response = self.client.post(reverse("offers:accept", args=[offer.pk]))
        self.assertRedirects(response, offer.get_absolute_url())
        offer.refresh_from_db()
        self.assertEqual(offer.status, JobOffer.Status.ACCEPTED)

    def test_accept_via_get_not_allowed(self):
        offer = self.make_offer()
        self.client.force_login(self.candidate)
        response = self.client.get(reverse("offers:accept", args=[offer.pk]))
        self.assertEqual(response.status_code, 405)

    def test_author_accept_via_post_is_403(self):
        offer = self.make_offer()
        self.client.force_login(self.evaluator)
        response = self.client.post(reverse("offers:accept", args=[offer.pk]))
        self.assertEqual(response.status_code, 403)

    def test_counter_via_post(self):
        offer = self.make_offer()
        self.client.force_login(self.candidate)
        response = self.client.post(reverse("offers:counter", args=[offer.pk]), {
            "salary": "31000",
            "modality": "hybrid",
            "message": "Me encaja con un poco más de salario.",
        })
        counter = JobOffer.objects.get(parent=offer)
        self.assertRedirects(response, counter.get_absolute_url())

    def test_invalid_counter_form_rerenders_detail(self):
        offer = self.make_offer()
        self.client.force_login(self.candidate)
        response = self.client.post(reverse("offers:counter", args=[offer.pk]), {
            "salary": "-5",
            "modality": "remote",
        })
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, "offers/detail.html")

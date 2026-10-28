from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class JobOffer(models.Model):
    """
    Oferta de empleo que un evaluador envía a un candidato a partir de una
    de sus evaluaciones. Cada contraoferta es una fila nueva enlazada con la
    anterior mediante ``parent``, de modo que se conserva todo el historial
    de la negociación.

    ``created_by`` indica quién hizo ESTA propuesta. La regla de oro es que
    sólo la otra parte puede aceptarla, rechazarla o contraofertarla, y sólo
    quien la creó puede cancelarla.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        ACCEPTED = "accepted", "Aceptada"
        REJECTED = "rejected", "Rechazada"
        CANCELLED = "cancelled", "Cancelada"
        COUNTERED = "countered", "Contraofertada"
        EXPIRED = "expired", "Caducada"

    class Modality(models.TextChoices):
        REMOTE = "remote", "Remoto"
        HYBRID = "hybrid", "Híbrido"
        ONSITE = "onsite", "Presencial"

    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="job_offers",
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_job_offers",
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_job_offers",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proposed_job_offers",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counter_offers",
    )

    position_title = models.CharField(max_length=150)
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Salario bruto anual en euros.",
    )
    modality = models.CharField(
        max_length=10,
        choices=Modality.choices,
        default=Modality.REMOTE,
    )
    message = models.TextField(blank=True, max_length=2000)

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["candidate", "status"], name="idx_offer_candidate_status"),
            models.Index(fields=["evaluator", "status"], name="idx_offer_evaluator_status"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(salary__gt=0),
                name="check_offer_salary_positive",
            ),
            models.CheckConstraint(
                condition=~models.Q(evaluator=models.F("candidate")),
                name="check_offer_not_self",
            ),
            # Sólo puede haber UNA negociación abierta por evaluación y candidato.
            models.UniqueConstraint(
                fields=["assessment", "candidate"],
                condition=models.Q(status="pending"),
                name="unique_pending_offer_per_assessment_candidate",
            ),
        ]

    def __str__(self):
        return (
            f"{self.position_title} ({self.evaluator.username} → "
            f"{self.candidate.username}) - {self.get_status_display()}"
        )

    def get_absolute_url(self):
        return reverse("offers:detail", kwargs={"pk": self.pk})

    # ------------------------------------------------------------------
    # Helpers de lectura (no cambian el estado: eso vive en services.py)
    # ------------------------------------------------------------------

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    @property
    def is_expired(self):
        return self.expires_at is not None and self.expires_at <= timezone.now()

    @property
    def is_counter(self):
        return self.parent_id is not None

    def is_participant(self, user):
        return user.pk in (self.evaluator_id, self.candidate_id)

    def other_party(self, user):
        return self.candidate if user.pk == self.evaluator_id else self.evaluator

    @property
    def awaiting_user(self):
        """Usuario que tiene que responder a esta propuesta."""
        if self.created_by_id == self.evaluator_id:
            return self.candidate
        return self.evaluator

    def can_respond(self, user):
        """Aceptar, rechazar o contraofertar: sólo la parte que NO la creó."""
        return (
            self.is_pending
            and not self.is_expired
            and self.is_participant(user)
            and user.pk != self.created_by_id
        )

    def can_cancel(self, user):
        return self.is_pending and user.pk == self.created_by_id

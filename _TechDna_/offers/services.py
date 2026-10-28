"""
Lógica de negocio de las ofertas de empleo.

Toda transición de estado pasa por aquí (nunca por las vistas ni por los
serializers) para que la API y la interfaz web apliquen exactamente las
mismas reglas. Cada operación:

1. Se ejecuta dentro de una transacción (``transaction.atomic``, o el
   decorador ``offer_transition`` que la envuelve).
2. Bloquea la fila implicada con ``select_for_update`` para que dos
   peticiones simultáneas (p. ej. aceptar y cancelar a la vez) no puedan
   dejar la oferta en un estado incoherente.
3. Vuelve a comprobar el estado DESPUÉS de bloquear la fila.

Errores:
- ``ValidationError``  -> la operación no es válida (400).
- ``PermissionDenied`` -> el usuario no puede hacer esa operación (403).
- ``JobOffer.DoesNotExist`` / ``Assessment.DoesNotExist`` -> 404.
"""

import logging
from functools import wraps
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from assessments.models import Assessment

from .models import JobOffer

logger = logging.getLogger(__name__)

User = get_user_model()

CANDIDATE_ROLE = "candidate"


# ----------------------------------------------------------------------
# Helpers internos
# ----------------------------------------------------------------------

def _clean_salary(salary):
    try:
        value = Decimal(str(salary))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError("El salario no es un número válido.")
    if value <= 0:
        raise ValidationError("El salario debe ser mayor que 0.")
    return value.quantize(Decimal("0.01"))


def _clean_modality(modality):
    if modality not in JobOffer.Modality.values:
        raise ValidationError("Modalidad de trabajo no válida.")
    return modality


def _clean_expires_at(expires_at):
    if expires_at is not None and expires_at <= timezone.now():
        raise ValidationError("La fecha de caducidad debe estar en el futuro.")
    return expires_at


def _lock_offer(offer_id):
    """Obtiene la oferta bloqueando su fila hasta el final de la transacción."""
    return JobOffer.objects.select_for_update().get(pk=offer_id)


class OfferExpired(ValidationError):
    """La oferta seguía PENDING pero su fecha de caducidad ya pasó."""

    def __init__(self, offer_id):
        super().__init__("La oferta ha caducado.")
        self.offer_id = offer_id


def offer_transition(func):
    """
    Ejecuta una transición de estado en su propia transacción.

    Si la oferta resulta estar caducada, la transacción se deshace (se lanza
    un error), así que la marcamos como EXPIRED FUERA de ella; si no, el
    rollback borraría también ese cambio. Es una caducidad "perezosa": no hace
    falta esperar a la tarea periódica para que el estado sea correcto.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with transaction.atomic():
                return func(*args, **kwargs)
        except OfferExpired as error:
            JobOffer.objects.filter(
                pk=error.offer_id,
                status=JobOffer.Status.PENDING,
            ).update(status=JobOffer.Status.EXPIRED, updated_at=timezone.now())
            raise

    return wrapper


def _ensure_pending(offer):
    """Comprueba que la oferta sigue abierta (y no ha caducado)."""
    if offer.status == JobOffer.Status.PENDING and offer.is_expired:
        raise OfferExpired(offer.pk)
    if offer.status != JobOffer.Status.PENDING:
        raise ValidationError(
            f"La oferta ya no está pendiente (estado: {offer.get_status_display()})."
        )


def _ensure_can_respond(user, offer):
    if not offer.is_participant(user):
        raise PermissionDenied("No participas en esta oferta.")
    if user.pk == offer.created_by_id:
        raise PermissionDenied("No puedes responder a tu propia propuesta.")


def _close(offer, new_status):
    offer.status = new_status
    offer.responded_at = timezone.now()
    offer.save(update_fields=["status", "responded_at", "updated_at"])
    return offer


# ----------------------------------------------------------------------
# Casos de uso
# ----------------------------------------------------------------------

@transaction.atomic
def create_offer(
    evaluator,
    assessment_id,
    candidate_id,
    position_title,
    salary,
    modality=JobOffer.Modality.REMOTE,
    message="",
    expires_at=None,
):
    """El propietario de una evaluación envía una oferta a un candidato."""
    # Bloqueamos la evaluación para serializar ofertas simultáneas sobre ella.
    assessment = Assessment.objects.select_for_update().get(pk=assessment_id)
    candidate = User.objects.get(pk=candidate_id)

    if assessment.owner_id != evaluator.pk:
        raise PermissionDenied(
            "Sólo el propietario de la evaluación puede enviar ofertas desde ella."
        )
    if not assessment.active:
        raise ValidationError("La evaluación no está activa.")
    if candidate.pk == evaluator.pk:
        raise ValidationError("No puedes enviarte una oferta a ti mismo.")
    if not candidate.is_active or candidate.role != CANDIDATE_ROLE:
        raise ValidationError("El destinatario debe ser un candidato activo.")

    position_title = (position_title or "").strip()
    if not position_title:
        raise ValidationError("El puesto es obligatorio.")

    if JobOffer.objects.filter(
        assessment=assessment,
        candidate=candidate,
        status=JobOffer.Status.PENDING,
    ).exists():
        raise ValidationError(
            "Ya hay una oferta pendiente para este candidato en esta evaluación."
        )

    try:
        # Savepoint propio: si salta la constraint, la transacción externa sigue usable.
        with transaction.atomic():
            offer = JobOffer.objects.create(
                assessment=assessment,
                evaluator=evaluator,
                candidate=candidate,
                created_by=evaluator,
                position_title=position_title,
                salary=_clean_salary(salary),
                modality=_clean_modality(modality),
                message=(message or "").strip(),
                expires_at=_clean_expires_at(expires_at),
            )
    except IntegrityError:
        # Carrera contra otra petición idéntica: la constraint parcial la frena.
        raise ValidationError(
            "Ya hay una oferta pendiente para este candidato en esta evaluación."
        )

    logger.info(
        "JobOffer created: id=%s assessment=%s evaluator=%s candidate=%s",
        offer.pk, assessment.pk, evaluator.pk, candidate.pk,
    )
    return offer


@offer_transition
def accept_offer(user, offer_id):
    """Acepta la propuesta. Sólo puede hacerlo la parte que NO la creó."""
    offer = _lock_offer(offer_id)
    _ensure_can_respond(user, offer)
    _ensure_pending(offer)
    _close(offer, JobOffer.Status.ACCEPTED)
    logger.info("JobOffer accepted: id=%s by=%s", offer.pk, user.pk)
    return offer


@offer_transition
def reject_offer(user, offer_id):
    """Rechaza la propuesta. Sólo puede hacerlo la parte que NO la creó."""
    offer = _lock_offer(offer_id)
    _ensure_can_respond(user, offer)
    _ensure_pending(offer)
    _close(offer, JobOffer.Status.REJECTED)
    logger.info("JobOffer rejected: id=%s by=%s", offer.pk, user.pk)
    return offer


@offer_transition
def cancel_offer(user, offer_id):
    """Retira la propuesta. Sólo puede hacerlo quien la creó."""
    offer = _lock_offer(offer_id)
    if not offer.is_participant(user):
        raise PermissionDenied("No participas en esta oferta.")
    if user.pk != offer.created_by_id:
        raise PermissionDenied("Sólo quien hizo la propuesta puede cancelarla.")
    _ensure_pending(offer)
    _close(offer, JobOffer.Status.CANCELLED)
    logger.info("JobOffer cancelled: id=%s by=%s", offer.pk, user.pk)
    return offer


@offer_transition
def counter_offer(user, offer_id, salary, modality=None, message="", expires_at=None):
    """
    Responde con nuevas condiciones. La propuesta original pasa a COUNTERED
    y se crea una nueva propuesta PENDING cuyo autor es ``user``; a partir
    de ahí es la otra parte quien debe responder.
    """
    offer = _lock_offer(offer_id)
    _ensure_can_respond(user, offer)
    _ensure_pending(offer)

    new_salary = _clean_salary(salary)
    new_modality = _clean_modality(modality or offer.modality)
    new_expires_at = _clean_expires_at(expires_at)
    if new_salary == offer.salary and new_modality == offer.modality:
        raise ValidationError(
            "La contraoferta debe cambiar el salario o la modalidad."
        )

    # Primero cerramos la original: así la constraint "una pendiente por
    # evaluación y candidato" permite crear la nueva.
    _close(offer, JobOffer.Status.COUNTERED)

    new_offer = JobOffer.objects.create(
        assessment_id=offer.assessment_id,
        evaluator_id=offer.evaluator_id,
        candidate_id=offer.candidate_id,
        created_by=user,
        parent=offer,
        position_title=offer.position_title,
        salary=new_salary,
        modality=new_modality,
        message=(message or "").strip(),
        expires_at=new_expires_at,
    )
    logger.info(
        "JobOffer countered: original=%s new=%s by=%s",
        offer.pk, new_offer.pk, user.pk,
    )
    return new_offer


def expire_pending_offers():
    """
    Marca como EXPIRED las ofertas pendientes cuya fecha de caducidad ya pasó.
    Pensada para ejecutarse periódicamente (Celery Beat, sesión 14).
    Devuelve el número de ofertas caducadas.
    """
    now = timezone.now()
    count = JobOffer.objects.filter(
        status=JobOffer.Status.PENDING,
        expires_at__isnull=False,
        expires_at__lte=now,
    ).update(status=JobOffer.Status.EXPIRED, updated_at=now)
    if count:
        logger.info("JobOffers expired: %s", count)
    return count


def get_negotiation_history(offer):
    """Devuelve la cadena de propuestas desde la primera hasta ``offer``."""
    chain = []
    current = offer
    while current is not None:
        chain.append(current)
        current = current.parent
    chain.reverse()
    return chain

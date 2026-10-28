from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from assessments.models import Assessment

from . import services
from .models import JobOffer
from .permissions import IsOfferParticipant
from .serializers import (
    CounterJobOfferInputSerializer,
    CreateJobOfferInputSerializer,
    JobOfferSerializer,
)

User = get_user_model()


def _error_response(error):
    """Traduce las excepciones de la capa de servicios a respuestas HTTP."""
    if isinstance(error, PermissionDenied):
        return Response({"detail": str(error)}, status=status.HTTP_403_FORBIDDEN)
    return Response({"detail": error.messages}, status=status.HTTP_400_BAD_REQUEST)


class JobOfferViewSet(
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    """
    Ofertas de empleo del usuario autenticado (enviadas y recibidas).

    Filtros: ``?status=pending`` y ``?box=received|sent``
    (received = propuestas que esperan MI respuesta, sent = propuestas MÍAS).
    """

    serializer_class = JobOfferSerializer
    permission_classes = [IsAuthenticated, IsOfferParticipant]
    filterset_fields = ["status", "assessment"]
    ordering_fields = ["created_at", "salary"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Swagger genera el esquema con un usuario anónimo.
        if getattr(self, "swagger_fake_view", False):
            return JobOffer.objects.none()

        user = self.request.user
        queryset = (
            JobOffer.objects
            .filter(Q(evaluator=user) | Q(candidate=user))
            .select_related("assessment", "evaluator", "candidate", "created_by")
        )
        box = self.request.query_params.get("box")
        if box == "sent":
            queryset = queryset.filter(created_by=user)
        elif box == "received":
            queryset = queryset.exclude(created_by=user)
        return queryset

    def _respond(self, offer, code=status.HTTP_200_OK):
        return Response(self.get_serializer(offer).data, status=code)

    @extend_schema(request=CreateJobOfferInputSerializer, responses=JobOfferSerializer)
    def create(self, request, *args, **kwargs):
        serializer = CreateJobOfferInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            offer = services.create_offer(
                evaluator=request.user,
                assessment_id=data["assessment"].pk,
                candidate_id=data["candidate"].pk,
                position_title=data["position_title"],
                salary=data["salary"],
                modality=data["modality"],
                message=data.get("message", ""),
                expires_at=data.get("expires_at"),
            )
        except (Assessment.DoesNotExist, User.DoesNotExist):
            return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except (PermissionDenied, ValidationError) as error:
            return _error_response(error)
        return self._respond(offer, status.HTTP_201_CREATED)

    # get_object() aplica el queryset (404 si no participas) Y los permisos
    # de objeto; por eso todas las acciones lo llaman antes del servicio.

    @extend_schema(request=None, responses=JobOfferSerializer)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        offer = self.get_object()
        try:
            offer = services.accept_offer(request.user, offer.pk)
        except (PermissionDenied, ValidationError) as error:
            return _error_response(error)
        return self._respond(offer)

    @extend_schema(request=None, responses=JobOfferSerializer)
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        offer = self.get_object()
        try:
            offer = services.reject_offer(request.user, offer.pk)
        except (PermissionDenied, ValidationError) as error:
            return _error_response(error)
        return self._respond(offer)

    @extend_schema(request=None, responses=JobOfferSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        offer = self.get_object()
        try:
            offer = services.cancel_offer(request.user, offer.pk)
        except (PermissionDenied, ValidationError) as error:
            return _error_response(error)
        return self._respond(offer)

    @extend_schema(request=CounterJobOfferInputSerializer, responses=JobOfferSerializer)
    @action(detail=True, methods=["post"])
    def counter(self, request, pk=None):
        offer = self.get_object()
        serializer = CounterJobOfferInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            new_offer = services.counter_offer(
                request.user,
                offer.pk,
                salary=data["salary"],
                modality=data.get("modality"),
                message=data.get("message", ""),
                expires_at=data.get("expires_at"),
            )
        except (PermissionDenied, ValidationError) as error:
            return _error_response(error)
        return self._respond(new_offer, status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """Cadena completa de propuestas hasta esta oferta."""
        offer = self.get_object()
        chain = services.get_negotiation_history(offer)
        return Response(self.get_serializer(chain, many=True).data)

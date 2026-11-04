from django.db.models import Count

from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from accounts.models import User
from accounts.services import get_candidates_nearby
from assessments.models import Assessment, Favorite
from skills.models import Technology, Role
from .serializers import (
    AssessmentSerializer,
    CandidateSerializer,
    TechnologySerializer,
    RoleSerializer,
    FavoriteSerializer,
)
from .permissions import IsOwnerOrReadOnly
from .filters import AssessmentFilter

class AssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar, crear, recuperar, actualizar y eliminar evaluaciones.
    """
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_class = AssessmentFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "favorites_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Assessment.objects.all()
            .select_related("owner", "technology", "role")
            .annotate(favorites_count=Count("favorites"))
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        assessment = self.get_object()
        if assessment.owner == request.user:
            return Response(
                {"detail": "No puedes guardar tu propia evaluación en favoritos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            assessment=assessment,
        )

        if created:
            return Response({"favorited": True}, status=status.HTTP_201_CREATED)

        favorite.delete()
        return Response({"favorited": False}, status=status.HTTP_200_OK)

class CandidateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Sesión 12: candidatos con búsqueda por proximidad (PostGIS).

    GET /api/v1/candidates/?lat=41.36&lng=2.11&distance_km=10
    Sin lat/lng devuelve todos los candidatos activos; con ellos, sólo los que
    están dentro del radio, ordenados por distancia. Sólo para usuarios
    autenticados: la ubicación es un dato personal.
    """
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["username", "city", "location_name"]
    filterset_fields = ["primary_track"]
    ordering_fields = ["username", "date_joined"]

    DEFAULT_DISTANCE_KM = 20
    MAX_DISTANCE_KM = 500

    def get_queryset(self):
        queryset = User.objects.filter(role="candidate", is_active=True).order_by("username")

        lat = self.request.query_params.get("lat")
        lng = self.request.query_params.get("lng")
        if not (lat and lng):
            return queryset

        try:
            lat = float(lat)
            lng = float(lng)
            distance_km = float(
                self.request.query_params.get("distance_km", self.DEFAULT_DISTANCE_KM)
            )
        except (TypeError, ValueError):
            raise ValidationError("lat, lng y distance_km deben ser numéricos.")

        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValidationError("Coordenadas fuera de rango.")
        if not (0 < distance_km <= self.MAX_DISTANCE_KM):
            raise ValidationError(
                f"distance_km debe estar entre 0 y {self.MAX_DISTANCE_KM}."
            )

        return get_candidates_nearby(lat, lng, radius_km=distance_km)

class TechnologyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Technology.objects.all().order_by("name")
    serializer_class = TechnologySerializer

class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.all().order_by("name")
    serializer_class = RoleSerializer

class FavoriteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related("assessment__owner", "assessment__technology", "assessment__role")
        )
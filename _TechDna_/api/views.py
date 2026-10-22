from django.db.models import Count

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from assessments.models import Assessment, Favorite
from skills.models import Technology, Role
from .serializers import (
    AssessmentSerializer,
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
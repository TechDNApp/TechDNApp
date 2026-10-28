from rest_framework.permissions import BasePermission


class IsOfferParticipant(BasePermission):
    """Sólo el evaluador y el candidato de la oferta pueden verla u operar con ella."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.is_participant(request.user)

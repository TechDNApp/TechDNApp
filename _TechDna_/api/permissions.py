from rest_framework.permissions import SAFE_METHODS, BasePermission

class IsOwnerOrReadOnly(BasePermission):
    """
    Permiso personalizado para permitir solo la lectura a cualquier usuario,
    pero permitiendo la escritura/edición únicamente al propietario del objeto.
    """
    def has_object_permission(self, request, view, obj):
        # Los métodos seguros (GET, HEAD, OPTIONS) están permitidos para cualquier solicitud
        if request.method in SAFE_METHODS:
            return True
        
        # La escritura solo se permite si el propietario del objeto es el usuario actual
        return obj.owner == request.user
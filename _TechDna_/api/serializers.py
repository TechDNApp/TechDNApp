from rest_framework import serializers
from assessments.models import Assessment, Favorite
from skills.models import Technology, Role
from accounts.models import User

class UserPublicSerializer(serializers.ModelSerializer):
    """Serializer público para exponer solo datos seguros del usuario/propietario."""
    class Meta:
        model = User
        fields = [
            "id",
            "username",
        ]

class CandidateSerializer(serializers.ModelSerializer):
    """
    Sesión 12: candidato con su ubicación y la distancia al punto buscado.

    Por privacidad no exponemos las coordenadas exactas del usuario: se
    redondean a 2 decimales (~1 km), suficiente para ubicarlo en un mapa.
    """
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "primary_track",
            "city",
            "location_name",
            "latitude",
            "longitude",
            "distance_km",
        ]
        read_only_fields = fields

    def get_latitude(self, obj):
        return round(obj.location.y, 2) if obj.location else None

    def get_longitude(self, obj):
        return round(obj.location.x, 2) if obj.location else None

    def get_distance_km(self, obj):
        distance = getattr(obj, "distance", None)
        return round(distance.km, 2) if distance is not None else None

class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = [
            "id",
            "name",
            "slug",
        ]

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "slug",
        ]

class AssessmentSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)
    technology_detail = TechnologySerializer(source="technology", read_only=True)
    role_detail = RoleSerializer(source="role", read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "owner",
            "title",
            "description",
            "technology",
            "technology_detail",
            "role",
            "role_detail",
            "favorites_count",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "favorites_count",
            "created_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["owner"] = request.user
        return super().create(validated_data)

        

class FavoriteSerializer(serializers.ModelSerializer):
    assessment = AssessmentSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = [
            "id",
            "assessment",
            "created_at",
        ]

    
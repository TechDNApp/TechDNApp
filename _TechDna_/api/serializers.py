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

    
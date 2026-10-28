from rest_framework.routers import DefaultRouter
from .views import (
    AssessmentViewSet,
    TechnologyViewSet,
    RoleViewSet,
    FavoriteViewSet,
)
from chat.views import ConversationViewSet

router = DefaultRouter()
router.register("assessments", AssessmentViewSet, basename="assessment")
router.register("technologies", TechnologyViewSet, basename="technology")
router.register("roles", RoleViewSet, basename="role")
router.register("favorites", FavoriteViewSet, basename="favorite")
router.register("conversations", ConversationViewSet, basename="conversation")

urlpatterns = router.urls
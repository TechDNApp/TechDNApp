from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'chat'

router = DefaultRouter()
router.register(r'api/conversations', views.ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('<int:pk>/', views.chat_detail, name='detail'),
    path('', include(router.urls)),
]
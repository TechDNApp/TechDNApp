from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('<int:pk>/', views.chat_detail, name='detail'),
]
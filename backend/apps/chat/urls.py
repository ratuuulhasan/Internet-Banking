from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatSessionViewSet, ChatAPIView, ChatStreamView

router = DefaultRouter()
router.register('sessions', ChatSessionViewSet, basename='chat-sessions')

urlpatterns = [
    path('ask/', ChatAPIView.as_view(), name='chat-ask'),
    path('stream/', ChatStreamView.as_view(), name='chat-stream'),
    path('', include(router.urls)),
]
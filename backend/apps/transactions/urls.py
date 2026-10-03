from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, TransferView

router = DefaultRouter()
router.register('', TransactionViewSet, basename='transactions')

urlpatterns = [
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('', include(router.urls)),
]
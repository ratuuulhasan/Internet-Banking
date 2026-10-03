from rest_framework.routers import DefaultRouter
from .views import KYCViewSet

router = DefaultRouter()
router.register('', KYCViewSet, basename='kyc')

urlpatterns = router.urls
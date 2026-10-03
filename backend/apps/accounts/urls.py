from rest_framework.routers import DefaultRouter
from .views import AccountViewSet

router = DefaultRouter()
router.register('', AccountViewSet, basename='accounts')

urlpatterns = router.urls
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Routes
    path('api/auth/', include('apps.users.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/transactions/', include('apps.transactions.urls')),
    path('api/beneficiaries/', include('apps.beneficiaries.urls')),
    path('api/otp/', include('apps.otp_service.urls')),
    path('api/kyc/', include('apps.kyc.urls')),
    path('api/bills/', include('apps.bills.urls')),
    path('api/cards/', include('apps.cards.urls')),
    path('api/loans/', include('apps.loans.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/complaints/', include('apps.complaints.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
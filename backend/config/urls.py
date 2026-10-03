from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def api_root(request):
    """Root API endpoint — health check + info"""
    return JsonResponse({
        "message": "🏦 Internet Banking API",
        "version": "1.0.0",
        "status": "running ✅",
        "documentation": "/api/docs/",
        "admin_panel": "/admin/",
        "endpoints": {
            "auth":          "/api/auth/",
            "accounts":      "/api/accounts/",
            "transactions":  "/api/transactions/",
            "beneficiaries": "/api/beneficiaries/",
            "otp":           "/api/otp/",
            "schema":        "/api/schema/",
            "docs":          "/api/docs/",
        }
    })


urlpatterns = [
    # Root — health check
    path('', api_root, name='api-root'),

    # Admin panel
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('apps.users.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/transactions/', include('apps.transactions.urls')),
    path('api/beneficiaries/', include('apps.beneficiaries.urls')),
    path('api/otp/', include('apps.otp_service.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
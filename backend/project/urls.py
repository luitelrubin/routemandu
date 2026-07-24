from django.contrib import admin
from django.urls import path, re_path, include
from debug_toolbar.toolbar import debug_toolbar_urls
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView,SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^auth/", include("djoser.urls")),
    re_path(r"^auth/", include("djoser.urls.jwt")),
    path("gtfs/", include("multigtfs.urls")),
    path("raptor/", include("raptor.urls")),
    path("api/users/", include("users.urls")),
    path("api/ptas/", include("ptas.urls")),
    # Optional: Profiler
    path('silk/', include('silk.urls', namespace='silk')),
    # Optional: Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + debug_toolbar_urls()
from django.contrib import admin
from django.urls import path, re_path, include
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^auth/", include("djoser.urls")),
    re_path(r"^auth/", include("djoser.urls.jwt")),
    path("gtfs/", include("multigtfs.urls")),
    path("raptor/", include("raptor.urls")),
    path("api/users/", include("users.urls")),
    path("api/ptas/", include("ptas.urls")),
    path('silk/', include('silk.urls', namespace='silk')),
] + debug_toolbar_urls()
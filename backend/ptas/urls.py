from rest_framework.routers import DefaultRouter

from ptas.views import PublicTransitAgencyViewSet

router = DefaultRouter()
router.register("", PublicTransitAgencyViewSet, basename="pta")

urlpatterns = router.urls

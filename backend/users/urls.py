from rest_framework.routers import DefaultRouter

from users.views import AdminUserViewSet

router = DefaultRouter()
router.register("", AdminUserViewSet, basename="admin-user")

urlpatterns = router.urls

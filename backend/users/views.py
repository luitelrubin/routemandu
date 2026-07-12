from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from users.serializers import AdminUserSerializer

User = get_user_model()


class AdminUserViewSet(ModelViewSet):
    """
    Admin-only user management (list/create/update/delete any user,
    including toggling is_staff/is_active). Used by the frontend admin
    panel. Regular self-service profile editing still goes through
    djoser's /auth/users/me/.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

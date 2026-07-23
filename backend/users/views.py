from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet
from djoser.conf import settings as djoser_settings
from django.contrib.auth.tokens import default_token_generator
from djoser.utils import encode_uid
import logging

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

    def perform_create(self, serializer):
        user = serializer.save()
        if djoser_settings.SEND_ACTIVATION_EMAIL:
            user.is_active = False
            user.save()

            uid = encode_uid(user.pk)
            token = default_token_generator.make_token(user)

            context = {
                "user": user,
                "uid": uid,
                "token": token,
            }

            # Create the email object
            email = djoser_settings.EMAIL.activation(self.request, context)

            # Send account activation email
            logger = logging.getLogger(__name__)
            try:
                email.send([user.email])
                logger.info(f"Account activation email sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send activation email: {e}")

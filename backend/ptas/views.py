from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from ptas.models import PublicTransitAgency
from ptas.permissions import IsAdminOrOwnPTA
from ptas.serializers import (
    PublicTransitAgencySerializer,
    PublicTransitAgencyOwnerSerializer,
)


class PublicTransitAgencyViewSet(ModelViewSet):
    """
    Admins: full CRUD over every agency (create/assign owner/delete).
    Agency owners: can only see and PATCH their own agency (name/color);
    they cannot create, delete, or reassign ownership.
    """

    queryset = PublicTransitAgency.objects.select_related("owner").all()
    permission_classes = [IsAdminOrOwnPTA]

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.all()
        if user.is_staff:
            return queryset
        return queryset.filter(owner=user)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return PublicTransitAgencySerializer
        return PublicTransitAgencyOwnerSerializer

    def get_permissions(self):
        # Only admins may create or delete agencies.
        if self.action in ("create", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()

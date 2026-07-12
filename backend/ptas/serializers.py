import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from ptas.models import PublicTransitAgency

User = get_user_model()

_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class OwnerSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class PublicTransitAgencySerializer(serializers.ModelSerializer):
    """
    - Admins can set/change `owner` (any user, as long as that user doesn't
      already own a different agency).
    - Agency owners can PATCH their own agency's name/color, but `owner`
      is read-only for them (enforced in the view via read-only field
      swap, see PublicTransitAgencyViewSet.get_serializer).
    """

    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    owner_detail = OwnerSummarySerializer(source="owner", read_only=True)

    class Meta:
        model = PublicTransitAgency
        fields = ("id", "name", "color", "owner", "owner_detail")

    def validate_color(self, value):
        if not _HEX_COLOR_RE.match(value):
            raise serializers.ValidationError(
                "Color must be a hex code like #1D4ED8."
            )
        return value

    def validate_owner(self, owner):
        existing = getattr(owner, "pta", None)
        if existing is not None and existing.pk != getattr(self.instance, "pk", None):
            raise serializers.ValidationError(
                f"{owner.email} already owns agency '{existing.name}'."
            )
        return owner


class PublicTransitAgencyOwnerSerializer(PublicTransitAgencySerializer):
    """Same fields, but `owner` can't be reassigned by the owner themself."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)

from djoser import serializers as djoser_serializers
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class PTASummarySerializer(serializers.Serializer):
    """Minimal agency info attached to a user's profile."""

    id = serializers.CharField()
    name = serializers.CharField()
    color = serializers.CharField()


class CustomUserSerializer(djoser_serializers.UserSerializer):
    """
    Used by djoser for /auth/users/me/ (read + self-update) and for the
    nested "user" representation elsewhere.

    NOTE: role/permission fields are read-only here on purpose. Without
    this, a logged-in (non-admin) user could PATCH their own profile with
    {"is_staff": true} and escalate themselves to admin, since djoser's
    "current user" permission (CurrentUserOrAdmin) allows self-updates.
    Role changes must go through the admin-only endpoint in this module.
    """

    pta = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
            "pta",
        )
        read_only_fields = (
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
        )

    def get_pta(self, user):
        pta = getattr(user, "pta", None)
        if pta is None:
            return None
        return PTASummarySerializer(pta).data


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    """
    Used by djoser for public self-registration (POST /auth/users/).

    Deliberately excludes is_staff/is_superuser/is_active so a self-signup
    request can never grant elevated privileges.
    """

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = User
        fields = ("id", "username", "email", "password")


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Full user management for admins only (see users.views.AdminUserViewSet).
    Allows setting is_staff/is_active and creating users with a password.
    """

    password = serializers.CharField(write_only=True, required=False, min_length=8)
    pta = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
            "last_login",
            "password",
            "pta",
        )
        read_only_fields = ("date_joined", "last_login")

    def get_pta(self, user):
        pta = getattr(user, "pta", None)
        if pta is None:
            return None
        return PTASummarySerializer(pta).data

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError(
                {"password": "Password is required when creating a user."}
            )
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

from rest_framework import permissions


class isPTA(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "pta", None)
        )


class IsAdminOrOwnPTA(permissions.BasePermission):
    """
    Admins can do anything. A PTA owner may only view/update the single
    PublicTransitAgency object that belongs to them (create/delete of
    agencies is admin-only, enforced separately in the view).
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_staff or getattr(user, "pta", None))
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        return getattr(obj, "owner_id", None) == user.id


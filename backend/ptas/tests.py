from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from ptas.models import PublicTransitAgency
from ptas.permissions import IsAdminOrOwnPTA, isPTA
from ptas.serializers import PublicTransitAgencySerializer

User = get_user_model()


def make_user(email, username=None, **extra):
    return User.objects.create_user(
        username=username or email.split("@")[0],
        email=email,
        password="testpass123",
        **extra,
    )


class PublicTransitAgencyModelTests(TestCase):
    def test_str_fields_and_owner_relation(self):
        owner = make_user("owner@example.com")
        pta = PublicTransitAgency.objects.create(
            id="sajha", name="Sajha Yatayat", color="#1D4ED8", owner=owner
        )
        self.assertEqual(pta.owner, owner)
        self.assertEqual(owner.pta, pta)

    def test_name_must_be_unique(self):
        owner1 = make_user("owner1@example.com")
        owner2 = make_user("owner2@example.com")
        PublicTransitAgency.objects.create(
            id="a", name="Same Name", color="#111111", owner=owner1
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PublicTransitAgency.objects.create(
                    id="b", name="Same Name", color="#222222", owner=owner2
                )

    def test_color_must_be_unique(self):
        owner1 = make_user("owner1@example.com")
        owner2 = make_user("owner2@example.com")
        PublicTransitAgency.objects.create(
            id="a", name="Agency A", color="#123456", owner=owner1
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PublicTransitAgency.objects.create(
                    id="b", name="Agency B", color="#123456", owner=owner2
                )

    def test_owner_is_one_to_one(self):
        owner = make_user("owner@example.com")
        PublicTransitAgency.objects.create(
            id="a", name="Agency A", color="#123456", owner=owner
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PublicTransitAgency.objects.create(
                    id="b", name="Agency B", color="#654321", owner=owner
                )


class PublicTransitAgencySerializerTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.other_user = make_user("other@example.com")

    def test_valid_hex_color_passes(self):
        serializer = PublicTransitAgencySerializer(
            data={
                "id": "sajha",
                "name": "Sajha Yatayat",
                "color": "#1D4ED8",
                "owner": self.owner.id,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_color_is_rejected(self):
        for bad_color in ["1D4ED8", "#1D4ED", "#GGGGGG", "red"]:
            serializer = PublicTransitAgencySerializer(
                data={
                    "id": "sajha",
                    "name": "Sajha Yatayat",
                    "color": bad_color,
                    "owner": self.owner.id,
                }
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("color", serializer.errors)

    def test_owner_who_already_owns_a_different_agency_is_rejected(self):
        PublicTransitAgency.objects.create(
            id="existing", name="Existing Agency", color="#111111", owner=self.owner
        )
        serializer = PublicTransitAgencySerializer(
            data={
                "id": "new-agency",
                "name": "New Agency",
                "color": "#222222",
                "owner": self.owner.id,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("owner", serializer.errors)

    def test_updating_existing_agencys_own_owner_is_allowed(self):
        pta = PublicTransitAgency.objects.create(
            id="existing", name="Existing Agency", color="#111111", owner=self.owner
        )
        serializer = PublicTransitAgencySerializer(
            instance=pta,
            data={
                "id": "existing",
                "name": "Existing Agency Renamed",
                "color": "#111111",
                "owner": self.owner.id,
            },
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class PtaPermissionsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = make_user("owner@example.com")
        self.admin = make_user("admin@example.com", is_staff=True)
        self.stranger = make_user("stranger@example.com")
        self.pta = PublicTransitAgency.objects.create(
            id="sajha", name="Sajha Yatayat", color="#1D4ED8", owner=self.owner
        )

    def test_isPTA_true_only_for_agency_owner(self):
        request = self.factory.get("/")
        request.user = self.owner
        self.assertTrue(isPTA().has_permission(request, None))

        request.user = self.stranger
        self.assertFalse(isPTA().has_permission(request, None))

    def test_is_admin_or_own_pta_object_permission(self):
        perm = IsAdminOrOwnPTA()
        request = self.factory.get("/")

        request.user = self.admin
        self.assertTrue(perm.has_object_permission(request, None, self.pta))

        request.user = self.owner
        self.assertTrue(perm.has_object_permission(request, None, self.pta))

        request.user = self.stranger
        self.assertFalse(perm.has_object_permission(request, None, self.pta))


class PublicTransitAgencyViewSetTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.other_owner = make_user("other_owner@example.com")
        self.admin = make_user("admin@example.com", is_staff=True)
        self.stranger = make_user("stranger@example.com")

        self.pta = PublicTransitAgency.objects.create(
            id="sajha", name="Sajha Yatayat", color="#1D4ED8", owner=self.owner
        )
        self.other_pta = PublicTransitAgency.objects.create(
            id="mayur", name="Mayur Yatayat", color="#F59E0B", owner=self.other_owner
        )

    def list_url(self):
        return reverse("pta-list")

    def detail_url(self, pk):
        return reverse("pta-detail", args=[pk])

    def test_anonymous_user_forbidden(self):
        response = self.client.get(self.list_url())
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_admin_sees_all_agencies(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_owner_only_sees_own_agency(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], "sajha")

    def test_stranger_without_pta_is_forbidden(self):
        self.client.force_authenticate(self.stranger)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_patch_own_name_and_color(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            self.detail_url("sajha"), {"name": "Sajha Renamed"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pta.refresh_from_db()
        self.assertEqual(self.pta.name, "Sajha Renamed")

    def test_owner_cannot_patch_another_agency(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            self.detail_url("mayur"), {"name": "Hijacked"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_cannot_reassign_owner_field(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            self.detail_url("sajha"), {"owner": self.stranger.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pta.refresh_from_db()
        # Owner field is read-only for non-admins, so it stays unchanged.
        self.assertEqual(self.pta.owner, self.owner)

    def test_owner_cannot_create_agency(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.list_url(),
            {
                "id": "new",
                "name": "New Agency",
                "color": "#333333",
                "owner": self.owner.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_cannot_delete_agency(self):
        self.client.force_authenticate(self.owner)
        response = self.client.delete(self.detail_url("sajha"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_agency(self):
        self.client.force_authenticate(self.admin)
        new_owner = make_user("new_owner@example.com")
        response = self.client.post(
            self.list_url(),
            {
                "id": "new",
                "name": "New Agency",
                "color": "#333333",
                "owner": new_owner.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PublicTransitAgency.objects.filter(id="new").exists())

    def test_admin_can_delete_agency(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.detail_url("sajha"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PublicTransitAgency.objects.filter(id="sajha").exists())

    def test_admin_can_reassign_owner(self):
        self.client.force_authenticate(self.admin)
        new_owner = make_user("new_owner2@example.com")
        response = self.client.patch(
            self.detail_url("sajha"), {"owner": new_owner.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pta.refresh_from_db()
        self.assertEqual(self.pta.owner, new_owner)

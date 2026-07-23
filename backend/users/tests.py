from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ptas.models import PublicTransitAgency
from users.serializers import AdminUserSerializer, CustomUserSerializer

User = get_user_model()


class CustomUserManagerTests(TestCase):
    def test_create_user_sets_hashed_password(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="s3cret123"
        )
        self.assertEqual(user.email, "alice@example.com")
        self.assertTrue(user.check_password("s3cret123"))
        self.assertNotEqual(user.password, "s3cret123")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(username="alice", email="", password="s3cret123")

    def test_create_user_without_username_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username="", email="alice@example.com", password="s3cret123"
            )

    def test_create_superuser_sets_staff_and_superuser_flags(self):
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="s3cret123"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_rejects_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="s3cret123",
                is_staff=False,
            )

    def test_email_is_normalized(self):
        user = User.objects.create_user(
            username="bob", email="Bob@EXAMPLE.com", password="s3cret123"
        )
        self.assertEqual(user.email, "Bob@example.com")


class CustomUserModelTests(TestCase):
    def test_str_returns_email(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="s3cret123"
        )
        self.assertEqual(str(user), "alice@example.com")

    def test_email_field_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertEqual(User.REQUIRED_FIELDS, ["username"])


class UserSerializerTests(TestCase):
    def test_custom_user_serializer_hides_pta_when_none(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="s3cret123"
        )
        data = CustomUserSerializer(user).data
        self.assertIsNone(data["pta"])
        self.assertNotIn("password", data)

    def test_custom_user_serializer_exposes_pta_summary(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="s3cret123"
        )
        PublicTransitAgency.objects.create(
            id="sajha", name="Sajha Yatayat", color="#1D4ED8", owner=user
        )
        data = CustomUserSerializer(user).data
        self.assertEqual(data["pta"]["id"], "sajha")
        self.assertEqual(data["pta"]["name"], "Sajha Yatayat")

    def test_custom_user_serializer_is_staff_is_read_only(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="s3cret123"
        )
        serializer = CustomUserSerializer(
            instance=user, data={"is_staff": True}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        # is_staff is read-only, so self-service update can't escalate privileges.
        self.assertFalse(updated.is_staff)

    def test_admin_user_serializer_create_requires_password(self):
        serializer = AdminUserSerializer(
            data={"username": "carol", "email": "carol@example.com"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(Exception):
            serializer.save()

    def test_admin_user_serializer_create_hashes_password(self):
        serializer = AdminUserSerializer(
            data={
                "username": "carol",
                "email": "carol@example.com",
                "password": "s3cret123",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertTrue(user.check_password("s3cret123"))
        self.assertNotEqual(user.password, "s3cret123")

    def test_admin_user_serializer_update_can_change_password(self):
        user = User.objects.create_user(
            username="carol", email="carol@example.com", password="oldpass123"
        )
        serializer = AdminUserSerializer(
            instance=user, data={"password": "newpass456"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertTrue(updated.check_password("newpass456"))

    def test_admin_user_serializer_update_without_password_keeps_it(self):
        user = User.objects.create_user(
            username="carol", email="carol@example.com", password="oldpass123"
        )
        serializer = AdminUserSerializer(
            instance=user, data={"first_name": "Carol"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertTrue(updated.check_password("oldpass123"))
        self.assertEqual(updated.first_name, "Carol")

    def test_admin_user_serializer_can_set_is_staff(self):
        serializer = AdminUserSerializer(
            data={
                "username": "dave",
                "email": "dave@example.com",
                "password": "s3cret123",
                "is_staff": True,
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertTrue(user.is_staff)


class AdminUserViewSetTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="s3cret123"
        )
        self.regular_user = User.objects.create_user(
            username="alice", email="alice@example.com", password="s3cret123"
        )

    def list_url(self):
        return reverse("admin-user-list")

    def detail_url(self, pk):
        return reverse("admin-user-detail", args=[pk])

    def test_anonymous_user_forbidden(self):
        response = self.client.get(self.list_url())
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_non_admin_forbidden(self):
        self.client.force_authenticate(self.regular_user)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_create_user_and_activation_email_is_sent(self):
        self.client.force_authenticate(self.admin)
        mail.outbox = []
        response = self.client.post(
            self.list_url(),
            {
                "username": "newbie",
                "email": "newbie@example.com",
                "password": "s3cret123",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(email="newbie@example.com")
        # SEND_ACTIVATION_EMAIL=True means new users start inactive.
        self.assertFalse(user.is_active)

    def test_admin_can_toggle_is_active(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            self.detail_url(self.regular_user.id), {"is_active": False}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

    def test_admin_can_delete_user(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.detail_url(self.regular_user.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())

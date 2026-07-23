import traceback
from datetime import datetime

from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status

from multigtfs import models
from multigtfs import serializers

from ptas.models import PublicTransitAgency
from ptas.permissions import isPTA


from rest_framework.views import APIView

# Marker stored in Feed.meta to identify the single admin-managed, multi-agency
# "system" GTFS feed, as opposed to a feed scoped to one PTA's agency name.
SYSTEM_FEED_META = {"scope": "system"}


def _is_system_feed(feed):
    return isinstance(feed.meta, dict) and feed.meta.get("scope") == "system"


def _system_feed_queryset():
    """Feeds marked as the system-wide, multi-agency feed.

    Filtered in Python rather than via a DB-level JSON lookup, since the
    underlying JSONField implementation's querying support for exact-value
    matches varies by backend/version.
    """
    ids = [f.id for f in models.Feed.objects.all().only("id", "meta") if _is_system_feed(f)]
    return models.Feed.objects.filter(id__in=ids)


class GTFSImportView(APIView):
    """
    Manage GTFS feed (upload, export, delete, metadata).

    - PTA owners manage for their own agency implicitly (request.user.pta).
    - Admins may specify which agency the feed belongs to via `pta_id` (form
      field on POST) or `pta_id` query param (GET/DELETE), to manage a single
      agency's feed exactly like a PTA owner would.
    - Admins may instead omit `pta_id` entirely to manage the system-wide
      GTFS feed, which may contain details for any number of agencies at
      once (i.e. a GTFS zip whose agency.txt lists multiple agencies).
    """

    parser_classes = (MultiPartParser,)
    permission_classes = [isPTA | IsAdminUser]
    # serializers = serializers.FeedSerializer

    def get(self, request, *args, **kwargs):
        """Retrieve GTFS feed metadata or export the GTFS feed as a zip file"""
        pta = getattr(request.user, "pta", None)
        system_scope = False
        if pta is None:
            pta_id = request.query_params.get("pta_id")
            if pta_id:
                try:
                    pta = PublicTransitAgency.objects.get(pk=pta_id)
                except PublicTransitAgency.DoesNotExist:
                    return Response(
                        {"error": f"Unknown agency id: {pta_id}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            elif request.user.is_superuser or request.user.is_staff:
                system_scope = True

        if not pta and not system_scope:
            return Response(
                {"error": "No agency associated with user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if system_scope:
            feed = _system_feed_queryset().order_by("-created").first()
            export_filename = "system_gtfs.zip"
        else:
            feed = models.Feed.objects.filter(agency__name=pta.name).first()
            export_filename = f'{pta.name.replace(" ", "_")}_gtfs.zip'

        if request.query_params.get("export") == "true":
            if not feed:
                return Response(
                    {"error": "No feed found to export"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            import io
            from django.http import FileResponse
            buffer = io.BytesIO()
            feed.export_gtfs(buffer)
            buffer.seek(0)
            response = FileResponse(buffer, content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{export_filename}"'
            return response

        if feed:
            payload = {
                "id": feed.id,
                "name": feed.name,
                "created": feed.created,
                "exists": True,
            }
            if system_scope:
                payload["agencies"] = list(
                    models.Agency.objects.filter(feed=feed).values("id", "name")
                )
            return Response(payload)
        return Response({"exists": False})

    def post(self, request, *args, **kwargs):
        """Upload and import a GTFS file"""

        file = request.FILES.get("feed")
        name = request.data.get("name", f"Imported at {datetime.now()}")

        if not file:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Resolve which agency this feed belongs to.
        pta = getattr(request.user, "pta", None)
        system_scope = False
        if pta is None:
            pta_id = request.data.get("pta_id")
            if pta_id:
                try:
                    pta = PublicTransitAgency.objects.get(pk=pta_id)
                except PublicTransitAgency.DoesNotExist:
                    return Response(
                        {"error": f"Unknown agency id: {pta_id}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            elif request.user.is_superuser or request.user.is_staff:
                # Admin uploading without a pta_id: this is a system-wide GTFS
                # feed, which may describe any number of agencies at once
                # (an agency.txt with multiple rows), rather than one PTA's feed.
                system_scope = True
            else:
                return Response(
                    {"error": "pta_id is required when an admin uploads a feed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            # Clear output timetable cache
            import shutil
            from django.conf import settings
            import os
            output_dir = os.path.join(settings.BASE_DIR, "output")
            if os.path.exists(output_dir):
                try:
                    shutil.rmtree(output_dir)
                except Exception:
                    pass

            if system_scope:
                # Replace the single system-wide feed entirely.
                _system_feed_queryset().delete()
                feed = models.Feed.objects.create(name=name, meta=SYSTEM_FEED_META)
                feed.import_gtfs(file)

                # Update trip short names to reflect whichever agencies run them.
                for a in models.Agency.objects.filter(feed=feed):
                    models.Trip.objects.filter(route__agency=a).update(short_name=a.name)
            else:
                # Delete old feeds for this agency
                old_feeds = models.Feed.objects.filter(agency__name=pta.name)
                if old_feeds.exists():
                    old_feeds.delete()

                # Create new feed
                feed = models.Feed.objects.create(name=name)
                feed.import_gtfs(file)

                # if non-admin users are uploading the feed
                if not request.user.is_superuser:
                    # Ensure PTA owners upload feed for their agency only
                    agency = models.Agency.objects.filter(feed=feed).first()
                    if agency:
                        agency.name = pta.name
                        agency.email = pta.owner.email
                        agency.save()

                    feed_info = models.FeedInfo.objects.filter(feed=feed).first()
                    if feed_info:
                        feed_info.contact_email = pta.owner.email
                        feed_info.publisher_name = pta.name
                        feed_info.save()

                    models.Trip.objects.filter(route__agency=agency).update(short_name=agency.name)
                else:
                    # update trip short names to reflect the agencies that run them
                    agencies = models.Agency.objects.all()
                    for a in agencies:
                        models.Trip.objects.filter(route__agency=a).update(short_name=a.name)

            return Response(
                {
                    "id": feed.id,
                    "name": feed.name,
                    "message": "GTFS imported successfully",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Delete GTFS feed and associated database records for agency"""
        pta = getattr(request.user, "pta", None)
        system_scope = False
        if pta is None:
            pta_id = request.data.get("pta_id") or request.query_params.get("pta_id")
            if pta_id:
                try:
                    pta = PublicTransitAgency.objects.get(pk=pta_id)
                except PublicTransitAgency.DoesNotExist:
                    return Response(
                        {"error": f"Unknown agency id: {pta_id}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            elif request.user.is_superuser or request.user.is_staff:
                system_scope = True

        if not pta and not system_scope:
            return Response(
                {"error": "No agency associated with user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if system_scope:
            old_feeds = _system_feed_queryset()
        else:
            old_feeds = models.Feed.objects.filter(agency__name=pta.name)

        if old_feeds.exists():
            old_feeds.delete()

            # Clear output timetable cache
            import shutil
            from django.conf import settings
            import os
            output_dir = os.path.join(settings.BASE_DIR, "output")
            if os.path.exists(output_dir):
                try:
                    shutil.rmtree(output_dir)
                except Exception:
                    pass

            return Response(
                {"message": "GTFS feed deleted successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "No feed found for this agency"},
            status=status.HTTP_404_NOT_FOUND,
        )

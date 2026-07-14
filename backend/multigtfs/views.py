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

class GTFSImportView(APIView):
    """
    Manage GTFS feed (upload, export, delete, metadata).

    - PTA owners manage for their own agency implicitly (request.user.pta).
    - Admins must specify which agency the feed belongs to via `pta_id` or `pta_id` query param.
    """

    parser_classes = (MultiPartParser,)
    permission_classes = [isPTA | IsAdminUser]

    def get(self, request, *args, **kwargs):
        """Retrieve GTFS feed metadata or export the GTFS feed as a zip file"""
        pta = getattr(request.user, "pta", None)
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

        if not pta:
            return Response(
                {"error": "No agency associated with user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        feed = models.Feed.objects.filter(agency__name=pta.name).first()

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
            response["Content-Disposition"] = f'attachment; filename="{pta.name.replace(" ", "_")}_gtfs.zip"'
            return response

        if feed:
            return Response({
                "id": feed.id,
                "name": feed.name,
                "created": feed.created,
                "exists": True
            })
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
        if pta is None:
            pta_id = request.data.get("pta_id")
            if not pta_id:
                return Response(
                    {"error": "pta_id is required when an admin uploads a feed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                pta = PublicTransitAgency.objects.get(pk=pta_id)
            except PublicTransitAgency.DoesNotExist:
                return Response(
                    {"error": f"Unknown agency id: {pta_id}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            # Delete old feeds for this agency
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

            # Create new feed
            feed = models.Feed.objects.create(name=name)
            feed.import_gtfs(file)
            agency = models.Agency.objects.filter(feed=feed).first()

            if agency:
                # agency.name = pta.name
                agency.email = pta.owner.email
                agency.save()
            feed_info = models.FeedInfo.objects.filter(feed=feed).first()
            if feed_info:
                feed_info.contact_email = pta.owner.email
                feed_info.publisher_name = pta.name
                feed_info.save()

            agencies = models.Agency.objects.all()  # only for admin
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

        if not pta:
            return Response(
                {"error": "No agency associated with user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

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


class GTFSImportView(CreateAPIView):
    """
    Upload + import a GTFS zip.

    - PTA owners upload for their own agency implicitly (request.user.pta).
    - Admins must specify which agency the feed belongs to via `pta_id`,
      since they don't have a `.pta` of their own.
    """

    parser_classes = (MultiPartParser,)
    queryset = models.Feed.objects.all()
    permission_classes = [isPTA | IsAdminUser]
    serializer_class = serializers.FeedSerializer

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
            if old_feeds:
                old_feeds.delete()

            # Create new feed
            feed = models.Feed.objects.create(name=name)
            feed.import_gtfs(file)
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

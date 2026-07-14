from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from multigtfs.models import Stop

from raptor.serializers import serialize_journey
from raptor.services import query_journey, InvalidDateError, UnknownStationError


class StationSearchView(APIView):
    """
    GET /raptor/stations/?q=<text>&limit=10

    Returns stations (parent stops) matching `q` by name, with
    coordinates, for the frontend's origin/destination autocomplete and
    for placing markers on the map. `q` omitted/empty returns the first
    `limit` stations alphabetically, useful for an initial "browse" list.

    A "station" here is a multigtfs Stop with no parent_station, matching
    how raptor/gtfs/timetable.py builds RAPTOR stations - so the `name`
    returned is exactly what you should pass as `origin`/`destination` to
    /raptor/query/.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()

        try:
            limit = int(request.query_params.get("limit", 15))
        except ValueError:
            return Response(
                {"detail": "'limit' must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limit = max(1, min(limit, 50))

        stations = Stop.objects.filter(parent_station__isnull=True)
        if query:
            stations = stations.filter(name__icontains=query)
        stations = stations.order_by("name")[:limit]

        results = [
            {
                "id": station.id,
                "name": station.name,
                "lat": station.point[1] if station.point else None,
                "lon": station.point[0] if station.point else None,
            }
            for station in stations
        ]
        return Response(results)


class RaptorQueryView(APIView):
    """
    GET /raptor/query/?origin=<station>&destination=<station>&time=08:35:00&rounds=5&date=20260712

    Runs the RAPTOR algorithm (same logic as `manage.py query_algorithm`)
    and returns the best journey as trip legs + GeoJSON shapes, ready to
    plot on a frontend map.

    Query params:
    - origin (required): origin station name
    - destination (required): destination station name
    - time: departure time as hh:mm:ss (default 08:35:00)
    - rounds: number of RAPTOR rounds (default 5)
    - input: cache directory holding the timetable (default "output")
    - date: service date as yyyymmdd. If given, builds/loads the timetable
      for that specific date (filtering trips by GTFS calendar validity),
      caching it under <input>/<date>/. If omitted, falls back to the
      static cached timetable at <input>/timetable.pcl.
    """

    # Override the project-wide JWT-required default so this endpoint can
    # be hit directly from the frontend. Remove this if the route should
    # require authentication like the rest of the API.
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        origin_station = request.query_params.get("origin")
        destination_station = request.query_params.get("destination")
        departure_time = request.query_params.get("time", "08:35:00")
        departure_date = request.query_params.get("date")
        input_folder = request.query_params.get("input", "output")

        if not origin_station or not destination_station:
            return Response(
                {"detail": "Both 'origin' and 'destination' query params are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rounds_param = request.query_params.get("rounds", "5")
        try:
            rounds = int(rounds_param)
        except ValueError:
            return Response(
                {"detail": f"'rounds' must be an integer, got: {rounds_param!r}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            journey = query_journey(
                input_folder=input_folder,
                origin_station=origin_station,
                destination_station=destination_station,
                departure_time=departure_time,
                rounds=rounds,
                departure_date=departure_date
            )
        except InvalidDateError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except UnknownStationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            # e.g. malformed 'time' string
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if journey is None or len(journey) == 0:
            return Response(
                {"detail": f"No journey found from {origin_station} to {destination_station}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(serialize_journey(journey))

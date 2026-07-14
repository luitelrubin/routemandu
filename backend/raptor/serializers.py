"""
Serializers for exposing RAPTOR journeys via the API.

Each leg gets its own "geometry": a GeoJSON LineString covering *only* the
path the rider actually travels on that leg (from their boarding stop to
their alighting stop) - not the trip's full route shape.

Using the trip's full multigtfs Trip.geometry (its complete
terminus-to-terminus shape) here would draw the entire route the bus/rail
runs, far beyond the rider's actual segment, which is both visually wrong
and - across a handful of legs on different routes - looks like almost the
whole network is highlighted on the map.

Geometry is built in three tiers, from best to worst available data:
1. Clip the trip's actual Shape (shapes.txt) between the two stops' GTFS
   `shape_dist_traveled` values, if the feed provides that field - this
   follows the real road/rail path.
2. If `shape_dist_traveled` isn't populated (common - it's optional),
   clip the Shape by finding the shape points nearest to each stop
   instead - still follows the real path, just located by proximity
   rather than distance-along-shape.
3. If the trip has no Shape at all, fall back to straight lines through
   the actual stops the trip makes between the two endpoints.
"""
from typing import Dict, List, Optional

from multigtfs.models import StopTime as GtfsStopTime, Trip as GtfsTrip

from raptor.models.structures import Journey


def serialize_journey(journey: Journey) -> Dict:
    """Serialize a Journey into a JSON-friendly dict; each leg carries its
    own `geometry` (or None for legs where one couldn't be resolved, e.g.
    a walking transfer with no trip)."""
    legs = [attach_leg_geometry(leg) for leg in journey.to_list()]

    return {
        "origin": journey.from_stop().station.name,
        "destination": journey.to_stop().station.name,
        "departure_time": journey.dep(),
        "arrival_time": journey.arr(),
        "duration": journey.travel_time(),
        "number_of_trips": journey.number_of_trips(),
        "legs": legs,
    }


def attach_leg_geometry(leg: Dict) -> Dict:
    """Add a `geometry` key (GeoJSON LineString or None) to a leg dict."""
    leg["geometry"] = build_leg_geometry(
        gtfs_trip_id=leg.get("gtfs_trip_id"),
        from_stop_id=leg.get("from_stop_id"),
        to_stop_id=leg.get("to_stop_id"),
        from_stop_idx=leg.get("from_stop_idx"),
        to_stop_idx=leg.get("to_stop_idx"),
    )
    return leg


def build_leg_geometry(
    gtfs_trip_id: Optional[int],
    from_stop_id: Optional[int],
    to_stop_id: Optional[int],
    from_stop_idx: Optional[int] = None,
    to_stop_idx: Optional[int] = None,
) -> Optional[Dict]:
    """Build a GeoJSON LineString for the from_stop -> to_stop portion of
    `gtfs_trip_id`. Returns None if it can't be resolved at all."""
    if gtfs_trip_id is None or from_stop_id is None or to_stop_id is None:
        return None

    # Fetch all StopTimes for this trip sorted by stop_sequence
    stop_times = list(
        GtfsStopTime.objects.filter(trip_id=gtfs_trip_id)
        .order_by("stop_sequence")
        .values("stop_id", "stop_sequence", "shape_dist_traveled", "stop__point")
    )

    if (
        from_stop_idx is not None
        and to_stop_idx is not None
        and from_stop_idx < len(stop_times)
        and to_stop_idx < len(stop_times)
    ):
        from_row = stop_times[from_stop_idx]
        to_row = stop_times[to_stop_idx]
    else:
        # Fallback
        stop_time_rows = {
            row["stop_id"]: row
            for row in stop_times
            if row["stop_id"] in [from_stop_id, to_stop_id]
        }
        if from_stop_id not in stop_time_rows or to_stop_id not in stop_time_rows:
            return None
        from_row = stop_time_rows[from_stop_id]
        to_row = stop_time_rows[to_stop_id]

    coordinates = _shape_subpath(gtfs_trip_id, from_row, to_row)
    if coordinates is None:
        lo, hi = sorted((from_row["stop_sequence"], to_row["stop_sequence"]))
        coordinates = _stop_to_stop_path(gtfs_trip_id, lo, hi)

    if not coordinates or len(coordinates) < 2:
        return None

    return {"type": "LineString", "coordinates": coordinates}


def _shape_subpath(gtfs_trip_id: int, from_row: dict, to_row: dict) -> Optional[List]:
    """Tier 1 & 2: clip the trip's Shape, by distance-traveled if
    available, else by nearest shape point to each stop. Returns None if
    the trip has no usable Shape."""
    trip = GtfsTrip.objects.filter(pk=gtfs_trip_id).select_related("shape").first()
    if trip is None or trip.shape_id is None:
        return None

    shape_points = list(
        trip.shape.points.order_by("sequence").values_list("point", "traveled")
    )
    if len(shape_points) < 2:
        return None

    from_dist = from_row["shape_dist_traveled"]
    to_dist = to_row["shape_dist_traveled"]

    if (
        from_dist is not None
        and to_dist is not None
        and all(traveled is not None for _, traveled in shape_points)
    ):
        lo, hi = sorted((from_dist, to_dist))
        coords = [
            [point[0], point[1]] for point, traveled in shape_points if lo <= traveled <= hi
        ]
        if len(coords) >= 2:
            return coords

    # Fall back to locating each stop by nearest shape point.
    from_point = from_row["stop__point"]
    to_point = to_row["stop__point"]
    if from_point is None or to_point is None:
        return None

    points_only = [p for p, _ in shape_points]
    from_idx = _nearest_point_index(points_only, from_point)
    to_idx = _nearest_point_index(points_only, to_point)
    lo_idx, hi_idx = sorted((from_idx, to_idx))
    coords = [[p[0], p[1]] for p in points_only[lo_idx : hi_idx + 1]]
    return coords if len(coords) >= 2 else None


def _nearest_point_index(points: List, target) -> int:
    """Index of the point in `points` closest to `target` (both (lon,
    lat)-like). Squared distance is fine here since we're only comparing,
    not measuring, and everything's within one city-scale shape."""
    best_idx, best_dist = 0, None
    tx, ty = target[0], target[1]
    for i, p in enumerate(points):
        dx, dy = p[0] - tx, p[1] - ty
        dist = dx * dx + dy * dy
        if best_dist is None or dist < best_dist:
            best_idx, best_dist = i, dist
    return best_idx


def _stop_to_stop_path(gtfs_trip_id: int, lo_seq: int, hi_seq: int) -> Optional[List]:
    """Tier 3: straight lines through the actual stops between the two
    sequence numbers (used when the trip has no Shape at all)."""
    stop_times = (  
        GtfsStopTime.objects.filter(
            trip_id=gtfs_trip_id, stop_sequence__gte=lo_seq, stop_sequence__lte=hi_seq
        )
        .select_related("stop")
        .order_by("stop_sequence")
    )
    return [
        [st.stop.point[0], st.stop.point[1]] for st in stop_times if st.stop.point is not None
    ]

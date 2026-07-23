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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from django.db.models import FloatField, Func
from multigtfs.models import ShapePoint, StopTime as GtfsStopTime, Trip as GtfsTrip

from ptas.models import PublicTransitAgency

from raptor.models.structures import Journey

# (lon, lat) as plain floats - deliberately NOT a GEOS Point. Indexing into
# a GEOS Point (p[0]/p[1]/.x/.y) round-trips through ctypes into libgeos on
# every access, which is fine once but disastrous inside a tight matching
# loop run over hundreds of shape points per leg. ST_X/ST_Y (below) pull
# the coordinates out as floats directly in SQL, so the loop never touches
# GEOS at all.
Coord = Tuple[float, float]


class _StX(Func):
    """PostGIS ST_X(point) -> float. Django doesn't ship a wrapper for
    this (there's no X()/Y() in django.contrib.gis.db.models.functions,
    despite that being an easy thing to assume exists - Func is the
    documented way to call a DB function Django doesn't wrap itself)."""

    function = "ST_X"
    output_field = FloatField()


class _StY(Func):
    """PostGIS ST_Y(point) -> float. See _StX."""

    function = "ST_Y"
    output_field = FloatField()


@dataclass
class _GeometryContext:
    """Everything build_leg_geometry() needs for every leg in a journey,
    fetched in 3 queries total up front rather than ~3 queries *per leg*.
    A 40-leg journey used to mean ~120 DB round trips just for geometry;
    each one pays full network latency, which dominates wall-clock time
    far more than any in-Python work does. Batching by `trip_id__in`/
    `shape_id__in` turns that into a fixed 3 queries no matter how many
    legs the journey has."""

    # trip_id -> that trip's StopTime rows, ordered by stop_sequence
    stop_times_by_trip: Dict[int, List[dict]] = field(default_factory=dict)
    # trip_id -> shape_id (or None if the trip has no shape)
    shape_id_by_trip: Dict[int, Optional[int]] = field(default_factory=dict)
    # shape_id -> that shape's (x, y, traveled) points, ordered by sequence
    shape_points_by_shape: Dict[int, List[Tuple[float, float, Optional[float]]]] = field(
        default_factory=dict
    )
    pta_color_by_trip: Dict[int, Optional[str]] = field(default_factory=dict)


def serialize_journey(journey: Journey) -> Dict:
    """Serialize a Journey into a JSON-friendly dict; each leg carries its
    own `geometry` (or None for legs where one couldn't be resolved, e.g.
    a walking transfer with no trip)."""
    leg_dicts = journey.to_list()
    context = _build_geometry_context(leg_dicts)
    legs = [attach_leg_geometry(leg, context) for leg in leg_dicts]

    return {
        "origin": journey.from_stop().station.name,
        "destination": journey.to_stop().station.name,
        "departure_time": journey.dep(),
        "arrival_time": journey.arr(),
        "duration": journey.travel_time(),
        "number_of_trips": journey.number_of_trips(),
        "legs": legs,
    }


def _build_geometry_context(legs: List[Dict]) -> _GeometryContext:
    """Batch-fetch StopTimes, Trip->Shape links, and ShapePoints for every
    distinct trip in the journey, in 3 queries total (see _GeometryContext
    docstring)."""
    trip_ids = {leg.get("gtfs_trip_id") for leg in legs} - {None}
    if not trip_ids:
        return _GeometryContext()

    stop_times_by_trip: Dict[int, List[dict]] = defaultdict(list)
    stop_time_rows = (
        GtfsStopTime.objects.filter(trip_id__in=trip_ids)
        .order_by("trip_id", "stop_sequence")
        .annotate(stop_x=_StX("stop__point"), stop_y=_StY("stop__point"))
        .values(
            "trip_id", "stop_id", "stop_sequence", "shape_dist_traveled", "stop_x", "stop_y"
        )
    )
    for row in stop_time_rows:
        stop_times_by_trip[row["trip_id"]].append(row)

    shape_id_by_trip: Dict[int, Optional[int]] = dict(
        GtfsTrip.objects.filter(pk__in=trip_ids).values_list("id", "shape_id")
    )
    shape_ids = {sid for sid in shape_id_by_trip.values() if sid is not None}

    shape_points_by_shape: Dict[int, List[Tuple[float, float, Optional[float]]]] = defaultdict(
        list
    )
    if shape_ids:
        shape_point_rows = (
            ShapePoint.objects.filter(shape_id__in=shape_ids)
            .order_by("shape_id", "sequence")
            .annotate(x=_StX("point"), y=_StY("point"))
            .values_list("shape_id", "x", "y", "traveled")
        )
        for shape_id, x, y, traveled in shape_point_rows:
            shape_points_by_shape[shape_id].append((x, y, traveled))
    agency_name_by_trip: Dict[int, Optional[str]] = dict(
        GtfsTrip.objects.filter(pk__in=trip_ids).values_list("id", "route__agency__name")
    )
    agency_names = {name for name in agency_name_by_trip.values() if name}
    color_by_agency_name: Dict[str, str] = dict(
        PublicTransitAgency.objects.filter(name__in=agency_names).values_list("name", "color")
    )
    pta_color_by_trip = {
        trip_id: color_by_agency_name.get(agency_name)
        for trip_id, agency_name in agency_name_by_trip.items()
    }

    return _GeometryContext(
        stop_times_by_trip=dict(stop_times_by_trip),
        shape_id_by_trip=shape_id_by_trip,
        shape_points_by_shape=dict(shape_points_by_shape),
        pta_color_by_trip=pta_color_by_trip
    )


def attach_leg_geometry(leg: Dict, context: Optional[_GeometryContext] = None) -> Dict:
    """Add a `geometry` key (GeoJSON LineString or None) to a leg dict."""
    if context is None:  # allow standalone use, e.g. from tests/a shell
        context = _build_geometry_context([leg])
    leg["geometry"] = build_leg_geometry(
        context=context,
        gtfs_trip_id=leg.get("gtfs_trip_id"),
        from_stop_id=leg.get("from_stop_id"),
        to_stop_id=leg.get("to_stop_id"),
        from_stop_idx=leg.get("from_stop_idx"),
        to_stop_idx=leg.get("to_stop_idx"),
    )
    leg["pta_color"] = context.pta_color_by_trip.get(leg.get("gtfs_trip_id"))
    return leg


def build_leg_geometry(
    context: _GeometryContext,
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

    stop_times = context.stop_times_by_trip.get(gtfs_trip_id, [])
    if not stop_times:
        return None

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

    coordinates = _shape_subpath(gtfs_trip_id, from_row, to_row, stop_times, context)
    if coordinates is None:
        lo, hi = sorted((from_row["stop_sequence"], to_row["stop_sequence"]))
        coordinates = _stop_to_stop_path(stop_times, lo, hi)

    if not coordinates or len(coordinates) < 2:
        return None

    return {"type": "LineString", "coordinates": coordinates}


def _shape_subpath(
    gtfs_trip_id: int,
    from_row: dict,
    to_row: dict,
    stop_times: List[dict],
    context: _GeometryContext,
) -> Optional[List]:
    """Tier 1 & 2: clip the trip's Shape, by distance-traveled if
    available, else by nearest shape point to each stop. Returns None if
    the trip has no usable Shape."""
    shape_id = context.shape_id_by_trip.get(gtfs_trip_id)
    if shape_id is None:
        return None

    # x/y pulled out in SQL as floats (see Coord comment) - shape_points
    # here is a list of (lon, lat, traveled) tuples, never GEOS Points.
    shape_points = context.shape_points_by_shape.get(shape_id, [])
    if len(shape_points) < 2:
        return None

    from_dist = from_row["shape_dist_traveled"]
    to_dist = to_row["shape_dist_traveled"]

    if (
        from_dist is not None
        and to_dist is not None
        and all(traveled is not None for _, _, traveled in shape_points)
    ):
        lo, hi = sorted((from_dist, to_dist))
        coords = [[x, y] for x, y, traveled in shape_points if lo <= traveled <= hi]
        if len(coords) >= 2:
            return coords

    # Fall back to locating each stop by nearest shape point. On a loop
    # (e.g. ring road) route, the shape's start and end are geographically
    # right next to each other, so matching each stop independently by
    # raw proximity is ambiguous - a stop near that seam can snap to the
    # wrong end of the shape and pull in the entire loop. Instead, walk
    # the shape forward in the trip's own stop order and never let a
    # later stop match to an earlier shape index than the stop before it,
    # using the (trusted) stop sequence to disambiguate the loop.
    if from_row["stop_x"] is None or to_row["stop_x"] is None:
        return None

    points_only: List[Coord] = [(x, y) for x, y, _ in shape_points]
    stop_to_shape_idx = _match_stops_to_shape(stop_times, points_only)
    from_idx = stop_to_shape_idx.get(from_row["stop_sequence"])
    to_idx = stop_to_shape_idx.get(to_row["stop_sequence"])
    if from_idx is None or to_idx is None:
        return None

    lo_idx, hi_idx = sorted((from_idx, to_idx))
    coords = [[x, y] for x, y in points_only[lo_idx : hi_idx + 1]]
    return coords if len(coords) >= 2 else None


def _match_stops_to_shape(
    stop_times: List[dict], shape_points: List[Coord]
) -> Dict[int, int]:
    """Map each stop (keyed by stop_sequence) in this trip to an index
    into `shape_points`, walking forward monotonically along the shape in
    stop order. This keeps loop routes from matching a stop near the
    shape's start/end seam to the wrong end of the polyline."""
    mapping: Dict[int, int] = {}
    search_start = 0
    for row in stop_times:  # already ordered by stop_sequence
        x, y = row.get("stop_x"), row.get("stop_y")
        if x is None or y is None:
            continue
        idx = _nearest_point_index(shape_points, (x, y), start_idx=search_start)
        mapping[row["stop_sequence"]] = idx
        search_start = idx
    return mapping


def _nearest_point_index(points: List[Coord], target: Coord, start_idx: int = 0) -> int:
    """Index of the point in `points[start_idx:]` closest to `target`
    (both (lon, lat) float tuples), never searching before `start_idx`.
    Squared distance is fine here since we're only comparing, not
    measuring, and everything's within one city-scale shape."""
    best_idx, best_dist = start_idx, None
    tx, ty = target
    for i in range(start_idx, len(points)):
        px, py = points[i]
        dx, dy = px - tx, py - ty
        dist = dx * dx + dy * dy
        if best_dist is None or dist < best_dist:
            best_idx, best_dist = i, dist
    return best_idx


def _stop_to_stop_path(stop_times: List[dict], lo_seq: int, hi_seq: int) -> Optional[List]:
    """Tier 3: straight lines through the actual stops between the two
    sequence numbers (used when the trip has no Shape at all). No query -
    `stop_times` was already fetched (with x/y) for the whole journey in
    _build_geometry_context, so this is just a filter over data we have."""
    return [
        [row["stop_x"], row["stop_y"]]
        for row in stop_times
        if lo_seq <= row["stop_sequence"] <= hi_seq and row["stop_x"] is not None
    ]

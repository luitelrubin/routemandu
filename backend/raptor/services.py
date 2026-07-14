"""
Service layer around the RAPTOR algorithm.

This wraps timetable loading + the round-based search so the same logic can
be reused from the `query_algorithm` management command and from the API
view, instead of duplicating it in both places.
"""
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from raptor.dao.timetable_io import read_timetable,write_timetable
from raptor.gtfs.timetable import read_gtfs_timetable, gtfs_to_pyraptor_timetable
from raptor.models.structures import Timetable, Journey
from raptor.models.raptor import (
    RaptorAlgorithm,
    reconstruct_journey,
    best_stop_at_target_station,
)
from raptor.util import str2sec


class UnknownStationError(KeyError):
    """Raised when an origin/destination station name can't be resolved."""

class InvalidDateError(ValueError):
    """Raised when a departure date isn't in yyyymmdd format."""

_DATE_RE = re.compile(r"^\d{8}$")

def validate_departure_date(departure_date: str) -> str:
    """Validate a departure date is in GTFS yyyymmdd format."""
    if not departure_date or not _DATE_RE.match(departure_date):
        raise InvalidDateError(
            f"'date' must be in yyyymmdd format, got: {departure_date!r}"
        )
    return departure_date

# @lru_cache(maxsize=32)
def get_timetable_for_date(base_folder: str, departure_date: str) -> Timetable:
    """
    Get the timetable valid for a specific GTFS service date (yyyymmdd).

    Mirrors what the `write_timetable` management command does: read trips/
    stop_times/etc. from the DB filtered to `departure_date`, build the
    RAPTOR Timetable, and cache it. Each date gets its own subfolder under
    `base_folder` (e.g. "output/20260712/timetable.pcl") so timetables for
    different dates don't clobber each other, and results are kept in
    memory (lru_cache) for the life of the process on top of that.
    """
    validate_departure_date(departure_date)

    date_folder = str(Path(base_folder) / departure_date)

    if Path(date_folder, "timetable.pcl").exists():
        return read_timetable(date_folder)

    gtfs_timetable = read_gtfs_timetable(departure_date)
    timetable = gtfs_to_pyraptor_timetable(gtfs_timetable)
    write_timetable(date_folder, timetable)

    return timetable


# @lru_cache(maxsize=8)
def get_timetable(input_folder: str) -> Timetable:
    """
    Load the cached timetable for `input_folder`, keeping it in memory for
    the lifetime of the process so repeated API calls don't re-read the
    pickle from disk every time.
    """
    return read_timetable(input_folder)

# @lru_cache(maxsize=32)
def get_timetable_for_date(base_folder: str, departure_date: str) -> Timetable:
    """
    Get the timetable valid for a specific GTFS service date (yyyymmdd).

    Mirrors what the `write_timetable` management command does: read trips/
    stop_times/etc. from the DB filtered to `departure_date`, build the
    RAPTOR Timetable, and cache it. Each date gets its own subfolder under
    `base_folder` (e.g. "output/20260712/timetable.pcl") so timetables for
    different dates don't clobber each other, and results are kept in
    memory (lru_cache) for the life of the process on top of that.
    """
    validate_departure_date(departure_date)

    date_folder = str(Path(base_folder) / departure_date)

    if Path(date_folder, "timetable.pcl").exists():
        return read_timetable(date_folder)

    gtfs_timetable = read_gtfs_timetable(departure_date)
    timetable = gtfs_to_pyraptor_timetable(gtfs_timetable)
    write_timetable(date_folder, timetable)

    return timetable

def run_raptor(
    timetable: Timetable,
    origin_station: str,
    dep_secs: int,
    rounds: int,
) -> Dict[int, Journey]:
    """
    Run the RAPTOR algorithm from `origin_station` and return the best
    Journey found to every reachable destination station, keyed by
    destination station id.
    """
    origin = timetable.stations.get(origin_station)
    if origin is None:
        raise UnknownStationError(f"Unknown origin station: {origin_station}")

    from_stops = origin.stops
    destination_stops = {station.id: station.stops for station in timetable.stations}
    destination_stops.pop(origin.id, None)
    # destination_stops = {station.name: station.stops for station in timetable.stations}
    # destination_stops.pop(origin.name, None)

    raptor = RaptorAlgorithm(timetable)
    bag_round_stop = raptor.run(from_stops, dep_secs, rounds)
    best_labels = bag_round_stop[max(bag_round_stop.keys())]

    journeys: Dict[int, Journey] = {}
    for destination_station_id, to_stops in destination_stops.items():
        dest_stop = best_stop_at_target_station(to_stops, best_labels)
        if dest_stop != 0:
            journeys[destination_station_id] = reconstruct_journey(dest_stop, best_labels)

    return journeys


def query_journey(
    input_folder: str,
    origin_station: str,
    destination_station: str,
    departure_time: str,
    rounds: int,
    departure_date: Optional[str] = None,
) -> Optional[Journey]:
    """
    Run RAPTOR from `origin_station` and return the Journey to
    `destination_station`, or None if no journey was found.

    Raises UnknownStationError if origin/destination can't be resolved.
    """
    if departure_date:
        timetable = get_timetable_for_date(input_folder, departure_date)
    else:
        timetable = get_timetable(input_folder)

    destination = timetable.stations.get(destination_station)
    if destination is None:
        raise UnknownStationError(f"Unknown destination station: {destination_station}")

    dep_secs = str2sec(departure_time)
    journeys = run_raptor(timetable, origin_station, dep_secs, rounds)

    return journeys.get(destination.id)

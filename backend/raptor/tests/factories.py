"""
Helpers for building tiny, fully in-memory RAPTOR ``Timetable`` objects for
tests, so the algorithm/service layer can be exercised without a database
or any GTFS files on disk.
"""
from raptor.models.structures import (
    Station,
    Stations,
    Stop,
    Stops,
    Timetable,
    Trip,
    Trips,
    TripStopTime,
    Routes,
    Transfers,
)
from raptor.util import str2sec


def build_simple_timetable():
    """
    Build a timetable with three stations (A, B, C) on a single route:

        A --(trip1, 08:00 -> 08:30)--> B --(trip1, 08:30 -> 09:00)--> C

    and a second, later trip on the same route:

        A --(trip2, 09:00 -> 09:30)--> B --(trip2, 09:30 -> 10:00)--> C

    No transfers are configured. Useful for exercising RaptorAlgorithm.run
    / services.run_raptor / services.query_journey without any DB access.
    """
    stations = Stations()
    stops = Stops()
    trips = Trips()
    routes = Routes()
    transfers = Transfers()

    station_a = stations.add(Station(id="A", name="Station A"))
    station_b = stations.add(Station(id="B", name="Station B"))
    station_c = stations.add(Station(id="C", name="Station C"))

    stop_a = stops.add(Stop(id="A_1", name="Station A", station=station_a))
    stop_b = stops.add(Stop(id="B_1", name="Station B", station=station_b))
    stop_c = stops.add(Stop(id="C_1", name="Station C", station=station_c))

    station_a.add_stop(stop_a)
    station_b.add_stop(stop_b)
    station_c.add_stop(stop_c)

    def make_trip(hint, dep_a, arr_b, dep_b, arr_c, gtfs_trip_id):
        trip = Trip(hint=hint, gtfs_trip_id=gtfs_trip_id)
        trip.add_stop_time(
            TripStopTime(
                trip=trip, stopidx=0, stop=stop_a,
                dts_arr=str2sec(dep_a), dts_dep=str2sec(dep_a),
            )
        )
        trip.add_stop_time(
            TripStopTime(
                trip=trip, stopidx=1, stop=stop_b,
                dts_arr=str2sec(arr_b), dts_dep=str2sec(dep_b),
            )
        )
        trip.add_stop_time(
            TripStopTime(
                trip=trip, stopidx=2, stop=stop_c,
                dts_arr=str2sec(arr_c), dts_dep=str2sec(arr_c),
            )
        )
        trips.add(trip)
        routes.add(trip)
        return trip

    make_trip("Trip 1", "08:00:00", "08:30:00", "08:30:00", "09:00:00", gtfs_trip_id=1)
    make_trip("Trip 2", "09:00:00", "09:30:00", "09:30:00", "10:00:00", gtfs_trip_id=2)

    return Timetable(
        stations=stations,
        stops=stops,
        trips=trips,
        trip_stop_times=None,
        routes=routes,
        transfers=transfers,
    )

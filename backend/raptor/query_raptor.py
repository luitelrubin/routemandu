"""Run query with RAPTOR algorithm"""
import argparse
from typing import Dict

from loguru import logger

from backend.raptor.dao.timetable_io import read_timetable
from raptor.models.structures import Journey, Station, Timetable
from raptor.models.raptor import (
    RaptorAlgorithm,
    reconstruct_journey,
    best_stop_at_target_station,
)
from raptor.util import str2sec


def parse_arguments():
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="output",
        help="Input directory",
    )
    parser.add_argument(
        "-or",
        "--origin",
        type=str,
        default="Hertogenbosch ('s)",
        help="Origin station of the journey",
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        default="Rotterdam Centraal",
        help="Destination station of the journey",
    )
    parser.add_argument(
        "-t", "--time", type=str, default="08:35:00", help="Departure time (hh:mm:ss)"
    )
    parser.add_argument(
        "-r",
        "--rounds",
        type=int,
        default=5,
        help="Number of rounds to execute the RAPTOR algorithm",
    )
    arguments = parser.parse_args()
    return arguments


def main(
    input_folder,
    origin_station,
    destination_station,
    departure_time,
    rounds,
):
    """Run RAPTOR algorithm"""

    logger.debug("Input directory     : {}", input_folder)
    logger.debug("Origin station      : {}", origin_station)
    logger.debug("Destination station : {}", destination_station)
    logger.debug("Departure time      : {}", departure_time)
    logger.debug("Rounds              : {}", str(rounds))

    timetable = read_timetable(input_folder)

    logger.info(f"Calculating network from: {origin_station}")

    # Departure time seconds
    dep_secs = str2sec(departure_time)
    logger.debug("Departure time (s.)  : " + str(dep_secs))

    # Find route between two stations
    journey_to_destinations = run_raptor(
        timetable,
        origin_station,
        dep_secs,
        rounds,
    )

    # Print journey to destination
    journey_to_destinations.get(destination_station).print(dep_secs=dep_secs)

def run_raptor(
    timetable: Timetable,
    origin_station: str,
    dep_secs: int,
    rounds: int,
) -> Dict[Station, Journey]:
    origin = timetable.stations.get(origin_station)
    if origin is None:
        raise KeyError(f"Unknown origin station: {origin_station}")

    from_stops = origin.stops

    destination_stops = {station.name: station.stops for station in timetable.stations}
    destination_stops.pop(origin.name, None)
    # Changes
    # destination_stops = {station.id: station.stops for station in timetable.stations}
    # destination_stops.pop(origin.id, None)

    raptor = RaptorAlgorithm(timetable)
    bag_round_stop = raptor.run(from_stops, dep_secs, rounds)
    # best_labels = bag_round_stop[rounds]
    best_labels = bag_round_stop[max(bag_round_stop.keys())]

    journey_to_destinations = dict()
    for destination_station_name, to_stops in destination_stops.items():
        dest_stop = best_stop_at_target_station(to_stops, best_labels)
        if dest_stop != 0:
            journey = reconstruct_journey(dest_stop, best_labels)
            journey_to_destinations[destination_station_name] = journey

    return journey_to_destinations

if __name__ == "__main__":
    args = parse_arguments()
    main(
        args.input,
        args.origin,
        args.destination,
        args.time,
        args.rounds,
    )
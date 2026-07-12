import logging
from django.core.management.base import BaseCommand, CommandError

from raptor.services import get_timetable, run_raptor, UnknownStationError
from raptor.util import str2sec


class Command(BaseCommand):
    help = "Run a query with the RAPTOR algorithm"

    def add_arguments(self, parser):
        parser.add_argument(
            "-i", "--input",
            type=str,
            dest="input_folder",
            default="output",
            help="Input directory containing cached timetable",
        )
        parser.add_argument(
            "-or", "--origin",
            type=str,
            dest="origin_station",
            required=True,
            help="Origin station of the journey",
        )
        parser.add_argument(
            "-d", "--destination",
            type=str,
            dest="destination_station",
            required=True,
            help="Destination station of the journey",
        )
        parser.add_argument(
            "-t", "--time",
            type=str,
            dest="departure_time",
            default="08:35:00",
            help="Departure time (hh:mm:ss)",
        )
        parser.add_argument(
            "-r", "--rounds",
            type=int,
            dest="rounds",
            default=5,
            help="Number of rounds to execute the RAPTOR algorithm",
        )

    def handle(self, *args, **options):
        # Setup logging
        verbosity = int(options["verbosity"])
        console = logging.StreamHandler(self.stderr)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        level = logging.WARNING if verbosity == 0 else (
            logging.INFO if verbosity == 1 else logging.DEBUG
        )
        console.setLevel(level)
        console.setFormatter(formatter)
        logger = logging.getLogger("raptor")
        logger.setLevel(level)
        logger.addHandler(console)

        input_folder = options["input_folder"]
        origin_station = options["origin_station"]
        destination_station = options["destination_station"]
        departure_time = options["departure_time"]
        rounds = options["rounds"]

        if not origin_station or not destination_station:
            raise CommandError("Both origin and destination stations are required")

        logger.debug("Input directory     : %s", input_folder)
        logger.debug("Origin station      : %s", origin_station)
        logger.debug("Destination station : %s", destination_station)
        logger.debug("Departure time      : %s", departure_time)
        logger.debug("Rounds              : %s", str(rounds))

        timetable = get_timetable(input_folder)

        dep_secs = str2sec(departure_time)
        logger.debug("Departure time (s.) : %s", str(dep_secs))

        try:
            journeys = run_raptor(timetable, origin_station, dep_secs, rounds)
        except UnknownStationError as exc:
            raise CommandError(str(exc)) from exc

        destination = timetable.stations.get(destination_station)
        if destination is None:
            raise CommandError(f"Unknown destination station: {destination_station}")

        journey = journeys.get(destination.id)
        if journey is None:
            self.stdout.write(self.style.WARNING(
                f"No journey found to {destination_station}"
            ))
            return

        journey.print(dep_secs=dep_secs)

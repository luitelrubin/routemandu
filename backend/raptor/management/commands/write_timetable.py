import logging
from django.core.management.base import BaseCommand, CommandError

from raptor.dao import write_timetable
from raptor.util import mkdir_if_not_exists
from raptor.models.structures import Timetable
from raptor.gtfs.timetable import (
    read_gtfs_timetable,
    gtfs_to_pyraptor_timetable,
)


class Command(BaseCommand):
    help = "Parse timetable from GTFS files and cache it"

    def add_arguments(self, parser):
        parser.add_argument(
            "-o", "--output",
            type=str,
            dest="output_folder",
            required=True,
            help="Output directory for cached timetable",
        )
        parser.add_argument(
            "-d", "--date",
            type=str,
            dest="departure_date",
            required=True,
            help="Departure date (yyyymmdd)",
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

        output_folder = options["output_folder"]
        departure_date = options["departure_date"]

        if not output_folder:
            raise CommandError("Output folder is required")
        if not departure_date:
            raise CommandError("Departure date is required")

        self.stdout.write(f"Parsing timetable for date {departure_date}...\n")
        mkdir_if_not_exists(output_folder)

        gtfs_timetable = read_gtfs_timetable(departure_date)
        timetable: Timetable = gtfs_to_pyraptor_timetable(gtfs_timetable)
        write_timetable(output_folder, timetable)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully cached timetable for {departure_date} to {output_folder}"
        ))


# import logging
# from django.core.management.base import BaseCommand, CommandError

# from raptor.dao import write_timetable
# from raptor.util import mkdir_if_not_exists
# from raptor.models.structures import Timetable
# from .timetable_helpers import (  # move your helper functions here
#     read_gtfs_timetable,
#     gtfs_to_pyraptor_timetable,
# )

# class Command(BaseCommand):
#     help = "Parse timetable from GTFS files and cache it"

#     def add_arguments(self, parser):
#         parser.add_argument(
#             "-i", "--input",
#             type=str,
#             default="data/input/KTM-gtfs",
#             help="Input directory containing GTFS files",
#         )
#         parser.add_argument(
#             "-o", "--output",
#             type=str,
#             default="data/output",
#             help="Output directory for cached timetable",
#         )
#         parser.add_argument(
#             "-d", "--date",
#             type=str,
#             default="20210906",
#             help="Departure date (yyyymmdd)",
#         )
#         parser.add_argument(
#             "-a", "--agencies",
#             nargs="+",
#             default=["NS"],
#             help="Agencies to include",
#         )
#         parser.add_argument(
#             "--icd",
#             action="store_true",
#             help="Add ICD fare(s)",
#         )

#     def handle(self, *args, **options):
#         # Setup logging
#         verbosity = int(options["verbosity"])
#         console = logging.StreamHandler(self.stderr)
#         formatter = logging.Formatter("%(levelname)s - %(message)s")
#         level = logging.WARNING if verbosity == 0 else (
#             logging.INFO if verbosity == 1 else logging.DEBUG
#         )
#         console.setLevel(level)
#         console.setFormatter(formatter)
#         logger = logging.getLogger("raptor")
#         logger.setLevel(level)
#         logger.addHandler(console)

#         input_folder = options["input"]
#         output_folder = options["output"]
#         departure_date = options["date"]
#         agencies = options["agencies"]
#         icd_fix = options["icd"]

#         self.stdout.write("Parsing timetable from GTFS files...\n")
#         mkdir_if_not_exists(output_folder)

#         gtfs_timetable = read_gtfs_timetable(input_folder, departure_date, agencies)
#         timetable: Timetable = gtfs_to_pyraptor_timetable(gtfs_timetable, icd_fix)
#         write_timetable(output_folder, timetable)

#         self.stdout.write(self.style.SUCCESS(
#             f"Successfully cached timetable to {output_folder}"
#         ))

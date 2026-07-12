"""Data access object for timetable (Django-integrated)"""
from pathlib import Path

from loguru import logger
import joblib

from raptor.models.structures import Timetable
from raptor.util import mkdir_if_not_exists


def read_timetable(input_folder: str) -> Timetable:
    """
    Read the timetable data from the cache directory.
    If cache is missing, rebuild from the database.
    """

    def load_joblib(name):
        logger.debug(f"Loading '{name}'")
        with open(Path(input_folder, f"{name}.pcl"), "rb") as handle:
            return joblib.load(handle)

    timetable_file = Path(input_folder, "timetable.pcl")

    if timetable_file.exists():
        logger.debug("Using cached timetable datastructure")
        timetable: Timetable = load_joblib("timetable")
    else:
        logger.info("Cached timetable not found, building from database...")
        # timetable: Timetable = build_timetable_from_db()
        write_timetable(input_folder, timetable)

    return timetable


def write_timetable(output_folder: str, timetable: Timetable) -> None:
    """
    Write the timetable to output directory
    """

    def write_joblib(state, name):
        with open(Path(output_folder, f"{name}.pcl"), "wb") as handle:
            joblib.dump(state, handle)

    logger.info("Write PyRaptor timetable to output directory")

    mkdir_if_not_exists(output_folder)
    write_joblib(timetable, "timetable")

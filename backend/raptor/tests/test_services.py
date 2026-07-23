from unittest.mock import patch

from django.test import SimpleTestCase

from raptor.services import (
    InvalidDateError,
    UnknownStationError,
    query_journey,
    run_raptor,
    validate_departure_date,
)
from raptor.tests.factories import build_simple_timetable
from raptor.util import str2sec


class ValidateDepartureDateTests(SimpleTestCase):
    def test_valid_date_is_returned_unchanged(self):
        self.assertEqual(validate_departure_date("20260712"), "20260712")

    def test_none_raises(self):
        with self.assertRaises(InvalidDateError):
            validate_departure_date(None)

    def test_empty_string_raises(self):
        with self.assertRaises(InvalidDateError):
            validate_departure_date("")

    def test_wrong_length_raises(self):
        with self.assertRaises(InvalidDateError):
            validate_departure_date("2026-07-12")

    def test_non_digit_raises(self):
        with self.assertRaises(InvalidDateError):
            validate_departure_date("2026071a")


class RunRaptorTests(SimpleTestCase):
    def setUp(self):
        self.timetable = build_simple_timetable()

    def test_finds_direct_and_multi_leg_journeys(self):
        journeys = run_raptor(
            self.timetable, "A", str2sec("07:50:00"), rounds=3
        )
        self.assertIn("B", journeys)
        self.assertIn("C", journeys)

        journey_to_b = journeys["B"]
        self.assertEqual(len(journey_to_b.legs), 1)
        self.assertEqual(journey_to_b.legs[0].from_stop.id, "A_1")
        self.assertEqual(journey_to_b.legs[0].to_stop.id, "B_1")

        journey_to_c = journeys["C"]
        self.assertEqual(len(journey_to_c.legs), 2)
        self.assertEqual(journey_to_c.legs[-1].to_stop.id, "C_1")
        # Arrives via the 08:00 trip, not the 09:00 one.
        self.assertEqual(journey_to_c.legs[-1].arr, str2sec("09:00:00"))

    def test_catches_the_later_trip_when_departing_after_the_first(self):
        journeys = run_raptor(
            self.timetable, "A", str2sec("08:45:00"), rounds=3
        )
        journey_to_b = journeys["B"]
        self.assertEqual(journey_to_b.legs[0].dep, str2sec("09:00:00"))
        self.assertEqual(journey_to_b.legs[0].arr, str2sec("09:30:00"))

    def test_unknown_origin_raises(self):
        with self.assertRaises(UnknownStationError):
            run_raptor(self.timetable, "NOPE", str2sec("08:00:00"), rounds=3)

    def test_destination_unreachable_within_rounds_is_absent(self):
        # 0 rounds means only the origin's own stop is ever marked, so
        # nothing beyond the origin should be reachable.
        journeys = run_raptor(self.timetable, "A", str2sec("07:50:00"), rounds=0)
        self.assertEqual(journeys, {})


class QueryJourneyTests(SimpleTestCase):
    def setUp(self):
        self.timetable = build_simple_timetable()
        patcher = patch(
            "raptor.services.get_timetable", return_value=self.timetable
        )
        self.mock_get_timetable = patcher.start()
        self.addCleanup(patcher.stop)

    def test_returns_journey_for_reachable_destination(self):
        journey = query_journey(
            input_folder="output",
            origin_station="A",
            destination_station="C",
            departure_time="07:50:00",
            rounds=3,
        )
        self.assertIsNotNone(journey)
        self.assertEqual(len(journey.legs), 2)
        self.mock_get_timetable.assert_called_once_with("output")

    def test_unknown_destination_raises(self):
        with self.assertRaises(UnknownStationError):
            query_journey(
                input_folder="output",
                origin_station="A",
                destination_station="NOPE",
                departure_time="07:50:00",
                rounds=3,
            )

    def test_unreachable_destination_returns_none(self):
        journey = query_journey(
            input_folder="output",
            origin_station="A",
            destination_station="C",
            departure_time="07:50:00",
            rounds=0,
        )
        self.assertIsNone(journey)

    def test_uses_dated_timetable_when_date_given(self):
        with patch(
            "raptor.services.get_timetable_for_date",
            return_value=self.timetable,
        ) as mock_get_for_date:
            journey = query_journey(
                input_folder="output",
                origin_station="A",
                destination_station="B",
                departure_time="07:50:00",
                rounds=3,
                departure_date="20260712",
            )
        self.assertIsNotNone(journey)
        mock_get_for_date.assert_called_once_with("output", "20260712")
        self.mock_get_timetable.assert_not_called()

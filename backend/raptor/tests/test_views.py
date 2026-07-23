from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from multigtfs.models import Feed, Stop
from raptor.models.structures import Journey, Leg, Stop as RaptorStop, Station, Trip, TripStopTime
from raptor.services import InvalidDateError, UnknownStationError


def _make_feed():
    return Feed.objects.create()


class StationSearchViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        feed = _make_feed()
        Stop.objects.create(
            feed=feed, stop_id="koteshowr", name="Koteshowr",
            point=Point(85.3346, 27.6819),
        )
        Stop.objects.create(
            feed=feed, stop_id="ratnapark", name="Ratnapark",
            point=Point(85.3128, 27.7040),
        )
        # A platform stop (has a parent station) - should never show up as
        # a "station" search result.
        parent = Stop.objects.create(
            feed=feed, stop_id="koteshowr-parent", name="Koteshowr Parent Station",
            point=Point(85.3346, 27.6819),
        )
        Stop.objects.create(
            feed=feed, stop_id="koteshowr-plat-1", name="Koteshowr Platform 1",
            point=Point(85.3346, 27.6819), parent_station=parent,
        )

    def test_no_query_returns_stations_alphabetically(self):
        response = self.client.get(reverse("raptor:stations"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [r["name"] for r in response.data]
        self.assertEqual(names, sorted(names))
        # Only stations (no parent_station) are ever returned.
        self.assertNotIn("Koteshowr Platform 1", names)

    def test_filters_by_query_case_insensitively(self):
        response = self.client.get(reverse("raptor:stations"), {"q": "kote"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [r["name"] for r in response.data]
        self.assertIn("Koteshowr", names)
        self.assertNotIn("Ratnapark", names)

    def test_result_shape_includes_coordinates(self):
        response = self.client.get(reverse("raptor:stations"), {"q": "Ratnapark"})
        result = response.data[0]
        self.assertEqual(result["name"], "Ratnapark")
        self.assertAlmostEqual(result["lat"], 27.7040, places=3)
        self.assertAlmostEqual(result["lon"], 85.3128, places=3)

    def test_limit_is_clamped(self):
        response = self.client.get(reverse("raptor:stations"), {"limit": "1000"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 50)

    def test_invalid_limit_returns_400(self):
        response = self.client.get(reverse("raptor:stations"), {"limit": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RaptorQueryViewTests(APITestCase):
    def _fake_journey(self):
        station_a = Station(id="A", name="Station A")
        station_b = Station(id="B", name="Station B")
        stop_a = RaptorStop(id="A_1", name="Station A", station=station_a)
        stop_b = RaptorStop(id="B_1", name="Station B", station=station_b)
        trip = Trip(hint="Trip 1", gtfs_trip_id=1)
        trip.add_stop_time(
            TripStopTime(trip=trip, stopidx=0, stop=stop_a, dts_arr=28800, dts_dep=28800)
        )
        trip.add_stop_time(
            TripStopTime(trip=trip, stopidx=1, stop=stop_b, dts_arr=30600, dts_dep=30600)
        )
        leg = Leg(
            from_stop=stop_a, to_stop=stop_b, trip=trip,
            earliest_arrival_time=30600, from_stop_idx=0, to_stop_idx=1,
        )
        return Journey(legs=[leg])

    def test_missing_params_returns_400(self):
        response = self.client.get(reverse("raptor:query"), {"origin": "A"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_rounds_returns_400(self):
        response = self.client.get(
            reverse("raptor:query"),
            {"origin": "A", "destination": "B", "rounds": "not-a-number"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("raptor.views.query_journey")
    def test_successful_query_returns_serialized_journey(self, mock_query_journey):
        mock_query_journey.return_value = self._fake_journey()
        response = self.client.get(
            reverse("raptor:query"), {"origin": "A", "destination": "B"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_query_journey.assert_called_once()
        _, kwargs = mock_query_journey.call_args
        self.assertEqual(kwargs["origin_station"], "A")
        self.assertEqual(kwargs["destination_station"], "B")

    @patch("raptor.views.query_journey")
    def test_no_journey_found_returns_404(self, mock_query_journey):
        mock_query_journey.return_value = None
        response = self.client.get(
            reverse("raptor:query"), {"origin": "A", "destination": "B"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("raptor.views.query_journey")
    def test_unknown_station_returns_404(self, mock_query_journey):
        mock_query_journey.side_effect = UnknownStationError("Unknown origin station: X")
        response = self.client.get(
            reverse("raptor:query"), {"origin": "X", "destination": "B"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("raptor.views.query_journey")
    def test_invalid_date_returns_400(self, mock_query_journey):
        mock_query_journey.side_effect = InvalidDateError("bad date")
        response = self.client.get(
            reverse("raptor:query"),
            {"origin": "A", "destination": "B", "date": "not-a-date"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

from django.test import SimpleTestCase

from raptor.util import str2sec, sec2str


class Str2SecTests(SimpleTestCase):
    def test_hh_mm_ss(self):
        self.assertEqual(str2sec("08:35:00"), 8 * 3600 + 35 * 60)

    def test_hh_mm_only(self):
        self.assertEqual(str2sec("08:35"), 8 * 3600 + 35 * 60)

    def test_midnight(self):
        self.assertEqual(str2sec("00:00:00"), 0)

    def test_strips_whitespace(self):
        self.assertEqual(str2sec("  08:35:00  "), 8 * 3600 + 35 * 60)

    def test_gtfs_after_midnight_hours(self):
        # GTFS allows hours >= 24 for trips that run past midnight.
        self.assertEqual(str2sec("25:10:00"), 25 * 3600 + 10 * 60)


class Sec2StrTests(SimpleTestCase):
    def test_default_hides_seconds(self):
        self.assertEqual(sec2str(8 * 3600 + 35 * 60 + 12), "08:35")

    def test_show_seconds(self):
        self.assertEqual(
            sec2str(8 * 3600 + 35 * 60 + 12, show_sec=True), "08:35:12"
        )

    def test_zero(self):
        self.assertEqual(sec2str(0), "00:00")

    def test_round_trip_with_str2sec(self):
        original = "14:07:00"
        self.assertEqual(sec2str(str2sec(original), show_sec=True), original)

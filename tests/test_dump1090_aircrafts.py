"""Test for the Dump1090 Aircrafts feed."""
import datetime
import requests
import unittest
from json import JSONDecodeError
from unittest import mock

from flightradar24_client.consts import UPDATE_OK, UPDATE_ERROR
from flightradar24_client.dump1090_aircrafts import Dump1090AircraftsFeed
from tests.utils import load_fixture


class TestDump1090AircraftsFeed(unittest.TestCase):
    """Test the Dump1090 Aircrafts Feed."""

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_ok(self, mock_session, mock_request):
        """Test updating feed is ok."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .return_value.ok = True
        mock_session.return_value.__enter__.return_value.send\
            .return_value.text = load_fixture('dump1090-aircrafts-1.json')

        feed = Dump1090AircraftsFeed(home_coordinates)
        assert repr(feed) == "<Dump1090AircraftsFeed(" \
                             "home=(-31.0, 151.0), " \
                             "url=http://localhost:8888/aircrafts.json, " \
                             "radius=None)>"
        status, entries = feed.update()
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 5

        feed_entry = entries['7c6d9a']
        assert feed_entry.external_id == "7c6d9a"
        assert feed_entry.coordinates == (-34.234888, 150.533009)
        self.assertAlmostEqual(feed_entry.distance_to_home, 362.4, 1)
        assert feed_entry.altitude == 13075
        assert feed_entry.callsign == "QLK231D"
        assert feed_entry.updated \
            == datetime.datetime(2018, 10, 26, 7, 35, 51, 400000,
                                 tzinfo=datetime.timezone.utc)
        assert feed_entry.speed == 357
        assert feed_entry.track == 61
        assert feed_entry.squawk == "7201"
        assert feed_entry.vert_rate == -1600

        assert repr(feed_entry) == "<Flightradar24FeedEntry(id=7c6d9a)>"

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_ok_filter_radius(self, mock_session, mock_request):
        """Test updating feed is ok with filter radius."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .return_value.ok = True
        mock_session.return_value.__enter__.return_value.send\
            .return_value.text = load_fixture('dump1090-aircrafts-1.json')

        feed = Dump1090AircraftsFeed(home_coordinates, filter_radius=300)
        assert repr(feed) == "<Dump1090AircraftsFeed(" \
                             "home=(-31.0, 151.0), " \
                             "url=http://localhost:8888/aircrafts.json, " \
                             "radius=300)>"
        status, entries = feed.update()
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 1

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_error(self, mock_session, mock_request):
        """Test updating feed results in error."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .return_value.ok = False

        feed = Dump1090AircraftsFeed(home_coordinates)
        status, entries = feed.update()
        assert status == UPDATE_ERROR

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_with_request_exception(self, mock_session, mock_request):
        """Test updating feed raises exception."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .side_effect = requests.exceptions.RequestException

        feed = Dump1090AircraftsFeed(home_coordinates)
        status, entries = feed.update()
        assert status == UPDATE_ERROR
        self.assertIsNone(entries)

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_with_json_decode_error(self, mock_session, mock_request):
        """Test updating feed raises exception."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .side_effect = JSONDecodeError("", "", 0)

        feed = Dump1090AircraftsFeed(home_coordinates)
        status, entries = feed.update()
        assert status == UPDATE_ERROR
        self.assertIsNone(entries)

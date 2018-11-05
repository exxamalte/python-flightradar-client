"""Test for the Flightsradar24 feed."""
import datetime
import requests
import unittest
from json import JSONDecodeError
from unittest import mock

from flightradar24_client.consts import UPDATE_OK, UPDATE_ERROR
from flightradar24_client.fr24_flights import Flightradar24FlightsFeed, \
    Flightradar24FlightsFeedAggregator
from flightradar24_client import FeedEntry
from tests.utils import load_fixture


class TestFlightradar24FlightsFeed(unittest.TestCase):
    """Test the Flightsradar24 feed."""

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_ok(self, mock_session, mock_request):
        """Test updating feed is ok."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .return_value.ok = True
        mock_session.return_value.__enter__.return_value.send\
            .return_value.text = load_fixture('fr24-flights-1.json')

        feed = Flightradar24FlightsFeed(home_coordinates)
        assert repr(feed) == "<Flightradar24FlightsFeed(" \
                             "home=(-31.0, 151.0), " \
                             "url=http://localhost:8754/flights.json, " \
                             "radius=None)>"
        status, entries = feed.update()
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 6

        feed_entry = entries['7C1469']
        assert feed_entry.external_id == "7C1469"
        assert feed_entry.coordinates == (-33.7779, 151.1324)
        self.assertAlmostEqual(feed_entry.distance_to_home, 309.1, 1)
        assert feed_entry.altitude == 2950
        assert feed_entry.callsign == "QFA456"
        assert feed_entry.updated \
            == datetime.datetime(2018, 10, 26, 7, 39, 51,
                                 tzinfo=datetime.timezone.utc)
        assert feed_entry.speed == 183
        assert feed_entry.track == 167
        assert feed_entry.squawk == "4040"
        assert feed_entry.vert_rate == -64

        assert repr(feed_entry) == "<Flightradar24FeedEntry(id=7C1469)>"

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_ok_filter_radius(self, mock_session, mock_request):
        """Test updating feed is ok with filter radius."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .return_value.ok = True
        mock_session.return_value.__enter__.return_value.send\
            .return_value.text = load_fixture('fr24-flights-1.json')

        feed = Flightradar24FlightsFeed(home_coordinates, filter_radius=300)
        assert repr(feed) == "<Flightradar24FlightsFeed(" \
                             "home=(-31.0, 151.0), " \
                             "url=http://localhost:8754/flights.json, " \
                             "radius=300)>"
        status, entries = feed.update()
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 2

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_error(self, mock_session, mock_request):
        """Test updating feed results in error."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .return_value.ok = False

        feed = Flightradar24FlightsFeed(home_coordinates)
        status, entries = feed.update()
        assert status == UPDATE_ERROR

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_update_with_request_exception(self, mock_session, mock_request):
        """Test updating feed raises exception."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .side_effect = requests.exceptions.RequestException

        feed = Flightradar24FlightsFeed(home_coordinates)
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

        feed = Flightradar24FlightsFeed(home_coordinates)
        status, entries = feed.update()
        assert status == UPDATE_ERROR
        self.assertIsNone(entries)

    @mock.patch("requests.Request")
    @mock.patch("requests.Session")
    def test_feed_aggregator(self, mock_session, mock_request):
        """Test updating feed through feed aggregator."""
        home_coordinates = (-31.0, 151.0)
        mock_session.return_value.__enter__.return_value.send\
            .return_value.ok = True

        feed_aggregator = Flightradar24FlightsFeedAggregator(home_coordinates)
        assert repr(feed_aggregator) == "<Flightradar24FlightsFeedAggregator" \
                                        "(feed=<Flightradar24FlightsFeed(" \
                                        "home=(-31.0, 151.0), " \
                                        "url=http://localhost:8754/" \
                                        "flights.json, " \
                                        "radius=None)>)>"

        # Update 1
        mock_session.return_value.__enter__.return_value.send\
            .return_value.text = load_fixture('fr24-flights-1.json')
        status, entries = feed_aggregator.update()
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 6

        feed_entry = entries['7C6B28']
        assert feed_entry.external_id == "7C6B28"
        assert feed_entry.coordinates == (-32.5470, 150.9698)
        assert feed_entry.altitude == 22175
        assert feed_entry.callsign == "JST423"

        assert repr(feed_entry) == "<Flightradar24FeedEntry(id=7C6B28)>"

        # Update 2
        mock_session.return_value.__enter__.return_value.send\
            .return_value.text = load_fixture('fr24-flights-2.json')
        status, entries = feed_aggregator.update()
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 6

        feed_entry = entries['7C6B28']
        assert feed_entry.external_id == "7C6B28"
        assert feed_entry.coordinates == (-32.5470, 150.9698)
        assert feed_entry.altitude == 22175
        assert feed_entry.callsign == "JST423"

    def test_entry_without_data(self):
        """Test simple entry without data."""
        entry = FeedEntry(None, None)
        self.assertIsNone(entry.coordinates)
        self.assertIsNone(entry.external_id)
        self.assertIsNone(entry.altitude)
        self.assertIsNone(entry.callsign)
        self.assertIsNone(entry.speed)
        self.assertIsNone(entry.track)
        self.assertIsNone(entry.squawk)
        self.assertIsNone(entry.vert_rate)
        self.assertIsNone(entry.updated)

"""Test for the Dump1090 Aircrafts feed."""
import aiohttp
import asyncio
from aioresponses import aioresponses
import datetime
import unittest

from flightradar24_client import FeedEntry
from flightradar24_client.consts import UPDATE_OK, UPDATE_ERROR
from flightradar24_client.dump1090_aircrafts import Dump1090AircraftsFeed, \
    Dump1090AircraftsFeedAggregator
from tests.utils import load_fixture


class TestDump1090AircraftsFeed(unittest.TestCase):
    """Test the Dump1090 Aircrafts Feed."""

    @aioresponses()
    def test_update_ok(self, mock_session):
        """Test updating feed is ok."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        mock_session.get('http://localhost:8888/data/aircraft.json',
                         status=200,
                         body=load_fixture('dump1090-aircrafts-1.json'))

        feed = Dump1090AircraftsFeed(home_coordinates)
        assert repr(feed) == "<Dump1090AircraftsFeed(" \
                             "home=(-31.0, 151.0), " \
                             "url=http://localhost:8888/data/" \
                             "aircraft.json, " \
                             "radius=None)>"
        status, entries = loop.run_until_complete(feed.update())
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

        assert repr(feed_entry) == "<FeedEntry(id=7c6d9a)>"

    @aioresponses()
    def test_update_ok_filter_radius(self, mock_session):
        """Test updating feed is ok with filter radius."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        mock_session.get('http://localhost:8888/data/aircraft.json',
                         status=200,
                         body=load_fixture('dump1090-aircrafts-1.json'))

        feed = Dump1090AircraftsFeed(home_coordinates, filter_radius=300)
        assert repr(feed) == "<Dump1090AircraftsFeed(" \
                             "home=(-31.0, 151.0), " \
                             "url=http://localhost:8888/data/" \
                             "aircraft.json, " \
                             "radius=300)>"
        status, entries = loop.run_until_complete(feed.update())
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 1

    @aioresponses()
    def test_update_error(self, mock_session):
        """Test updating feed results in error."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        mock_session.get('http://localhost:8888/data/aircraft.json',
                         status=500, body='ERROR')

        feed = Dump1090AircraftsFeed(home_coordinates)
        status, entries = loop.run_until_complete(feed.update())
        assert status == UPDATE_ERROR

    @aioresponses()
    def test_update_with_client_error(self, mock_session):
        """Test updating feed raises exception."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        mock_session.get('http://localhost:8888/data/aircraft.json',
                         exception=aiohttp.ClientError())

        feed = Dump1090AircraftsFeed(home_coordinates)
        status, entries = loop.run_until_complete(feed.update())
        assert status == UPDATE_ERROR
        self.assertIsNone(entries)

    @aioresponses()
    def test_update_with_timeout_error(self, mock_session):
        """Test updating feed raises exception."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        mock_session.get('http://localhost:8888/data/aircraft.json',
                         exception=asyncio.TimeoutError())

        feed = Dump1090AircraftsFeed(home_coordinates)
        status, entries = loop.run_until_complete(feed.update())
        assert status == UPDATE_ERROR
        self.assertIsNone(entries)

    @aioresponses()
    def test_feed_aggregator(self, mock_session):
        """Test updating feed through feed aggregator."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)

        feed_aggregator = Dump1090AircraftsFeedAggregator(home_coordinates)
        assert repr(feed_aggregator) == "<Dump1090AircraftsFeedAggregator" \
                                        "(feed=<Dump1090AircraftsFeed(" \
                                        "home=(-31.0, 151.0), " \
                                        "url=http://localhost:8888/" \
                                        "data/aircraft.json, " \
                                        "radius=None)>)>"

        # Update 1
        mock_session.get('http://localhost:8888/data/aircraft.json',
                         status=200,
                         body=load_fixture('dump1090-aircrafts-1.json'))
        status, entries = loop.run_until_complete(feed_aggregator.update())
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 5

        feed_entry = entries['7c6b28']
        assert feed_entry.external_id == "7c6b28"
        assert feed_entry.coordinates == (-32.819840, 151.124735)
        assert feed_entry.altitude == 26000
        assert feed_entry.callsign == "JST423"

        assert repr(feed_entry) == "<FeedEntry(id=7c6b28)>"

        # Update 2
        mock_session.get('http://localhost:8888/data/aircraft.json',
                         status=200,
                         body=load_fixture('dump1090-aircrafts-2.json'))
        status, entries = loop.run_until_complete(feed_aggregator.update())
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 5

        feed_entry = entries['7c6b28']
        assert feed_entry.external_id == "7c6b28"
        assert feed_entry.coordinates == (-32.819840, 151.124735)
        assert feed_entry.altitude == 26000
        assert feed_entry.callsign == "JST423"

    @aioresponses()
    def test_feed_aggregator_filter_radius(self, mock_session):
        """Test updating feed is ok with filter radius."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        mock_session.get('http://localhost:8888/data/aircraft.json',
                         status=200,
                         body=load_fixture('dump1090-aircrafts-1.json'))

        feed_aggregator = Dump1090AircraftsFeedAggregator(home_coordinates,
                                                          filter_radius=300)
        assert repr(feed_aggregator) == "<Dump1090AircraftsFeedAggregator" \
                                        "(feed=<Dump1090AircraftsFeed(" \
                                        "home=(-31.0, 151.0), " \
                                        "url=http://localhost:8888/" \
                                        "data/aircraft.json, " \
                                        "radius=300)>)>"

        status, entries = loop.run_until_complete(feed_aggregator.update())
        assert status == UPDATE_OK
        self.assertIsNotNone(entries)
        assert len(entries) == 1

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

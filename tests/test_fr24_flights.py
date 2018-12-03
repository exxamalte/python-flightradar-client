"""Test for the Flightsradar24 feed."""
import aiohttp
import asyncio
import asynctest
from aioresponses import aioresponses
import datetime

from flightradar_client import FeedEntry, FlightradarException
from flightradar_client.consts import UPDATE_OK, UPDATE_ERROR
from flightradar_client.fr24feed_flights import FlightradarFlightsFeed, \
    FlightradarFlightsFeedAggregator, FlightradarFlightsFeedManager
from tests.utils import load_fixture


class TestFlightradarFlightsFeed(asynctest.TestCase):
    """Test the Flightsradar24 feed."""

    @aioresponses()
    async def test_update_ok(self, mock_aioresponse):
        """Test updating feed is ok."""
        home_coordinates = (-31.0, 151.0)
        mock_aioresponse.get('http://localhost:8754/flights.json', status=200,
                             body=load_fixture('fr24-flights-1.json'))

        async with aiohttp.ClientSession() as session:
            feed = FlightradarFlightsFeed(home_coordinates, session)
            assert repr(feed) == "<FlightradarFlightsFeed(" \
                                 "home=(-31.0, 151.0), " \
                                 "url=http://localhost:8754/flights.json, " \
                                 "radius=None)>"
            status, entries = await feed.update()
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

            assert repr(feed_entry) == "<FeedEntry(id=7C1469)>"

    @aioresponses()
    async def test_update_custom_url(self, mock_aioresponse):
        """Test updating feed is ok with custom url."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        custom_url = 'http://something:9876/foo/bar.json'
        mock_aioresponse.get(custom_url, status=200,
                             body=load_fixture('fr24-flights-1.json'))

        async with aiohttp.ClientSession() as session:
            feed = FlightradarFlightsFeed(home_coordinates, session,
                                            url=custom_url)
            assert repr(feed) == "<FlightradarFlightsFeed(" \
                                 "home=(-31.0, 151.0), " \
                                 "url=http://something:9876/foo/bar.json, " \
                                 "radius=None)>"
            status, entries = await feed.update()
            assert status == UPDATE_OK
            self.assertIsNotNone(entries)
            assert len(entries) == 6

            feed_entry = entries['7C1469']
            assert feed_entry.external_id == "7C1469"

    @aioresponses()
    async def test_update_ok_filter_radius(self, mock_aioresponse):
        """Test updating feed is ok with filter radius."""
        home_coordinates = (-31.0, 151.0)
        mock_aioresponse.get('http://localhost:8754/flights.json', status=200,
                             body=load_fixture('fr24-flights-1.json'))

        async with aiohttp.ClientSession() as session:
            feed = FlightradarFlightsFeed(home_coordinates, session,
                                            filter_radius=300)
            assert repr(feed) == "<FlightradarFlightsFeed(" \
                                 "home=(-31.0, 151.0), " \
                                 "url=http://localhost:8754/flights.json, " \
                                 "radius=300)>"
            status, entries = await feed.update()
            assert status == UPDATE_OK
            self.assertIsNotNone(entries)
            assert len(entries) == 2

    @aioresponses()
    async def test_missing_session(self, mock_aioresponse):
        """Test updating feed without supplying client session."""
        home_coordinates = (-31.0, 151.0)
        mock_aioresponse.get('http://localhost:8754/flights.json', status=200,
                             body=load_fixture('fr24-flights-1.json'))

        async with aiohttp.ClientSession() as session:
            with self.assertRaises(FlightradarException):
                feed = FlightradarFlightsFeed(home_coordinates, None)

    @aioresponses()
    async def test_update_error(self, mock_aioresponse):
        """Test updating feed results in error."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        mock_aioresponse.get('http://localhost:8754/flights.json', status=500,
                             body='ERROR')

        async with aiohttp.ClientSession() as session:
            feed = FlightradarFlightsFeed(home_coordinates, session)
            status, entries = await feed.update()
            assert status == UPDATE_ERROR

    @aioresponses()
    async def test_update_with_client_error(self, mock_aioresponse):
        """Test updating feed raises exception."""
        loop = asyncio.get_event_loop()
        home_coordinates = (-31.0, 151.0)
        mock_aioresponse.get('http://localhost:8754/flights.json',
                             exception=aiohttp.ClientError())

        async with aiohttp.ClientSession() as session:
            feed = FlightradarFlightsFeed(home_coordinates, session)
            status, entries = await feed.update()
            assert status == UPDATE_ERROR
            self.assertIsNone(entries)

    @aioresponses()
    async def test_update_with_timeout_error(self, mock_aioresponse):
        """Test updating feed raises exception."""
        home_coordinates = (-31.0, 151.0)
        mock_aioresponse.get('http://localhost:8754/flights.json',
                             exception=asyncio.TimeoutError())

        async with aiohttp.ClientSession() as session:
            feed = FlightradarFlightsFeed(home_coordinates, session)
            status, entries = await feed.update()
            assert status == UPDATE_ERROR
            self.assertIsNone(entries)

    @aioresponses()
    async def test_feed_aggregator(self, mock_aioresponse):
        """Test updating feed through feed aggregator."""
        home_coordinates = (-31.0, 151.0)

        async with aiohttp.ClientSession() as session:
            feed_aggregator = FlightradarFlightsFeedAggregator(
                home_coordinates, session)
            assert repr(feed_aggregator) == "<FlightradarFlightsFeed" \
                                            "Aggregator" \
                                            "(feed=<FlightradarFlightsFeed(" \
                                            "home=(-31.0, 151.0), " \
                                            "url=http://localhost:8754/" \
                                            "flights.json, " \
                                            "radius=None)>)>"

            # Update 1
            mock_aioresponse.get('http://localhost:8754/flights.json',
                                 status=200,
                                 body=load_fixture('fr24-flights-1.json'))
            status, entries = await feed_aggregator.update()
            assert status == UPDATE_OK
            self.assertIsNotNone(entries)
            assert len(entries) == 5

            feed_entry = entries['7C6B28']
            assert feed_entry.external_id == "7C6B28"
            assert feed_entry.coordinates == (-32.5470, 150.9698)
            assert feed_entry.altitude == 22175
            assert feed_entry.callsign == "JST423"

            assert repr(feed_entry) == "<FeedEntry(id=7C6B28)>"

            # Update 2
            mock_aioresponse.get('http://localhost:8754/flights.json',
                                 status=200,
                                 body=load_fixture('fr24-flights-2.json'))
            status, entries = await feed_aggregator.update()
            assert status == UPDATE_OK
            self.assertIsNotNone(entries)
            assert len(entries) == 5

            feed_entry = entries['7C6B28']
            assert feed_entry.external_id == "7C6B28"
            assert feed_entry.coordinates == (-32.5470, 150.9698)
            assert feed_entry.altitude == 22175
            assert feed_entry.callsign == "JST423"

    @aioresponses()
    async def test_feed_aggregator_update_error(self, mock_aioresponse):
        """Test updating feed aggregator results in error."""
        home_coordinates = (-31.0, 151.0)
        mock_aioresponse.get('http://localhost:8754/flights.json', status=500,
                             body='ERROR')

        async with aiohttp.ClientSession() as session:
            feed_aggregator = FlightradarFlightsFeedAggregator(
                home_coordinates, session)
            status, entries = await feed_aggregator.update()
            assert status == UPDATE_ERROR
            self.assertIsNone(entries)

    @aioresponses()
    async def test_feed_manager(self, mock_aioresponse):
        """Test the feed manager."""
        home_coordinates = (-31.0, 151.0)
        mock_aioresponse.get('http://localhost:8754/flights.json', status=200,
                             body=load_fixture('fr24-flights-1.json'))

        # This will just record calls and keep track of external ids.
        generated_entity_external_ids = []
        updated_entity_external_ids = []
        removed_entity_external_ids = []

        async def _generate_entity(external_id):
            """Generate new entity."""
            generated_entity_external_ids.append(external_id)

        async def _update_entity(external_id):
            """Update entity."""
            updated_entity_external_ids.append(external_id)

        async def _remove_entity(external_id):
            """Remove entity."""
            removed_entity_external_ids.append(external_id)

        async with aiohttp.ClientSession() as session:
            feed_manager = FlightradarFlightsFeedManager(_generate_entity,
                                                         _update_entity,
                                                         _remove_entity,
                                                         home_coordinates,
                                                         session)
            assert repr(feed_manager) == "<FlightradarFlightsFeedManager(" \
                                         "feed=" \
                                         "<FlightradarFlightsFeed" \
                                         "Aggregator" \
                                         "(feed=<FlightradarFlightsFeed(" \
                                         "home=(-31.0, 151.0), " \
                                         "url=http://localhost:8754/" \
                                         "flights.json, " \
                                         "radius=None)>)>)>"
            await feed_manager.update(None)
            entries = feed_manager.feed_entries
            self.assertIsNotNone(entries)
            assert len(entries) == 5
            assert len(generated_entity_external_ids) == 5
            assert len(updated_entity_external_ids) == 0
            assert len(removed_entity_external_ids) == 0

            feed_entry = entries['7C1469']
            assert feed_entry.external_id == "7C1469"
            assert feed_entry.coordinates == (-33.7779, 151.1324)
            assert repr(feed_entry) == "<FeedEntry(id=7C1469)>"

            # Simulate an update with several changes.
            generated_entity_external_ids.clear()
            updated_entity_external_ids.clear()
            removed_entity_external_ids.clear()

            mock_aioresponse.get('http://localhost:8754/flights.json',
                                 status=200,
                                 body=load_fixture('fr24-flights-3.json'))

            await feed_manager.update(None)
            entries = feed_manager.feed_entries
            self.assertIsNotNone(entries)
            assert len(entries) == 5
            assert len(generated_entity_external_ids) == 1
            assert len(updated_entity_external_ids) == 4
            assert len(removed_entity_external_ids) == 1

            feed_entry = entries['7C1469']
            assert feed_entry.external_id == "7C1469"
            assert feed_entry.coordinates == (-33.8880, 151.2435)

            # Simulate an update with no data.
            generated_entity_external_ids.clear()
            updated_entity_external_ids.clear()
            removed_entity_external_ids.clear()

            mock_aioresponse.get('http://localhost:8754/flights.json',
                                 status=500,
                                 body='ERROR')

            await feed_manager.update(None)
            entries = feed_manager.feed_entries

            assert len(entries) == 0
            assert len(generated_entity_external_ids) == 0
            assert len(updated_entity_external_ids) == 0
            assert len(removed_entity_external_ids) == 5

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

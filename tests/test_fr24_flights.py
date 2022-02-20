"""Test for the Flightsradar24 feed."""
import asyncio
import datetime

import aiohttp
import pytest

from flightradar_client.consts import UPDATE_ERROR, UPDATE_OK
from flightradar_client.exceptions import FlightradarException
from flightradar_client.feed_entry import FeedEntry
from flightradar_client.fr24feed_flights import (
    FlightradarFlightsFeed,
    FlightradarFlightsFeedAggregator,
    FlightradarFlightsFeedManager,
)
from tests.utils import load_fixture


@pytest.mark.asyncio
async def test_update_ok(aresponses, event_loop):
    """Test updating feed is ok."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8754",
        "/flights.json",
        "get",
        aresponses.Response(
            text=load_fixture("fr24feed-flights-1.json"),
            content_type="application/json",
            status=200,
        ),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = FlightradarFlightsFeed(home_coordinates, websession)
        assert (
            repr(feed) == "<FlightradarFlightsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8754/flights.json, "
            "radius=None)>"
        )
        status, entries = await feed.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 6

        feed_entry = entries["7C1469"]
        assert feed_entry.external_id == "7C1469"
        assert feed_entry.coordinates == (-33.7779, 151.1324)
        assert feed_entry.distance_to_home == pytest.approx(309.1, rel=0.1)
        assert feed_entry.altitude == 2950
        assert feed_entry.callsign == "QFA456"
        assert feed_entry.updated == datetime.datetime(
            2018, 10, 26, 7, 39, 51, tzinfo=datetime.timezone.utc
        )
        assert feed_entry.speed == 183
        assert feed_entry.track == 167
        assert feed_entry.squawk == "4040"
        assert feed_entry.vert_rate == -64

        assert repr(feed_entry) == "<FeedEntry(id=7C1469)>"


@pytest.mark.asyncio
async def test_update_custom_url(aresponses, event_loop):
    """Test updating feed is ok with custom url."""
    home_coordinates = (-31.0, 151.0)
    custom_url = "http://something:9876/foo/bar.json"
    aresponses.add(
        "something:9876",
        "/foo/bar.json",
        "get",
        aresponses.Response(
            text=load_fixture("fr24feed-flights-1.json"),
            content_type="application/json",
            status=200,
        ),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = FlightradarFlightsFeed(home_coordinates, websession, url=custom_url)
        assert (
            repr(feed) == "<FlightradarFlightsFeed("
            "home=(-31.0, 151.0), "
            "url=http://something:9876/foo/bar.json, "
            "radius=None)>"
        )
        status, entries = await feed.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 6

        feed_entry = entries["7C1469"]
        assert feed_entry.external_id == "7C1469"


@pytest.mark.asyncio
async def test_update_ok_filter_radius(aresponses, event_loop):
    """Test updating feed is ok with filter radius."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8754",
        "/flights.json",
        "get",
        aresponses.Response(
            text=load_fixture("fr24feed-flights-1.json"),
            content_type="application/json",
            status=200,
        ),
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = FlightradarFlightsFeed(home_coordinates, websession, filter_radius=300)
        assert (
            repr(feed) == "<FlightradarFlightsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8754/flights.json, "
            "radius=300)>"
        )
        status, entries = await feed.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 2


@pytest.mark.asyncio
async def test_missing_session(aresponses, event_loop):
    """Test updating feed without supplying client session."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8754",
        "/flights.json",
        "get",
        aresponses.Response(
            text=load_fixture("fr24feed-flights-1.json"),
            content_type="application/json",
            status=200,
        ),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop):
        with pytest.raises(FlightradarException):
            FlightradarFlightsFeed(home_coordinates, None)


@pytest.mark.asyncio
async def test_update_error(aresponses, event_loop):
    """Test updating feed results in error."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8754",
        "/flights.json",
        "get",
        aresponses.Response(text="ERROR", status=500),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = FlightradarFlightsFeed(home_coordinates, websession)
        status, entries = await feed.update()
        assert status == UPDATE_ERROR


@pytest.mark.asyncio
async def test_update_with_client_error(aresponses, event_loop):
    """Test updating feed raises exception."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8754",
        "/flights.json",
        "get",
        aiohttp.ClientError(),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = FlightradarFlightsFeed(home_coordinates, websession)
        status, entries = await feed.update()
        assert status == UPDATE_ERROR
        assert entries is None


@pytest.mark.asyncio
async def test_update_with_timeout_error(aresponses, event_loop):
    """Test updating feed raises exception."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8754",
        "/flights.json",
        "get",
        asyncio.TimeoutError(),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = FlightradarFlightsFeed(home_coordinates, websession)
        status, entries = await feed.update()
        assert status == UPDATE_ERROR
        assert entries is None


@pytest.mark.asyncio
async def test_feed_aggregator(aresponses, event_loop):
    """Test updating feed through feed aggregator."""
    home_coordinates = (-31.0, 151.0)

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed_aggregator = FlightradarFlightsFeedAggregator(home_coordinates, websession)
        assert (
            repr(feed_aggregator) == "<FlightradarFlightsFeed"
            "Aggregator"
            "(feed=<FlightradarFlightsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8754/"
            "flights.json, "
            "radius=None)>)>"
        )

        # Update 1
        aresponses.add(
            "localhost:8754",
            "/flights.json",
            "get",
            aresponses.Response(
                text=load_fixture("fr24feed-flights-1.json"),
                content_type="application/json",
                status=200,
            ),
            match_querystring=True,
        )
        status, entries = await feed_aggregator.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 5

        feed_entry = entries["7C6B28"]
        assert feed_entry.external_id == "7C6B28"
        assert feed_entry.coordinates == (-32.5470, 150.9698)
        assert feed_entry.altitude == 22175
        assert feed_entry.callsign == "JST423"
        assert feed_entry.statistics is not None
        assert feed_entry.statistics.success_ratio() == 1.0

        assert repr(feed_entry) == "<FeedEntry(id=7C6B28)>"

        # Update 2
        aresponses.add(
            "localhost:8754",
            "/flights.json",
            "get",
            aresponses.Response(
                text=load_fixture("fr24feed-flights-2.json"),
                content_type="application/json",
                status=200,
            ),
            match_querystring=True,
        )
        status, entries = await feed_aggregator.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 5

        feed_entry = entries["7C6B28"]
        assert feed_entry.external_id == "7C6B28"
        assert feed_entry.coordinates == (-32.5470, 150.9698)
        assert feed_entry.altitude == 22175
        assert feed_entry.callsign == "JST423"


@pytest.mark.asyncio
async def test_feed_aggregator_update_error(aresponses, event_loop):
    """Test updating feed aggregator results in error."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8754",
        "/flights.json",
        "get",
        aresponses.Response(text="ERROR", status=500),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed_aggregator = FlightradarFlightsFeedAggregator(home_coordinates, websession)
        status, entries = await feed_aggregator.update()
        assert status == UPDATE_ERROR
        assert entries is None


@pytest.mark.asyncio
async def test_feed_manager(aresponses, event_loop):
    """Test the feed manager."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8754",
        "/flights.json",
        "get",
        aresponses.Response(
            text=load_fixture("fr24feed-flights-1.json"),
            content_type="application/json",
            status=200,
        ),
        match_querystring=True,
    )

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

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed_manager = FlightradarFlightsFeedManager(
            _generate_entity,
            _update_entity,
            _remove_entity,
            home_coordinates,
            websession,
        )
        assert (
            repr(feed_manager) == "<FlightradarFlightsFeedManager("
            "feed="
            "<FlightradarFlightsFeed"
            "Aggregator"
            "(feed=<FlightradarFlightsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8754/"
            "flights.json, "
            "radius=None)>)>)>"
        )
        await feed_manager.update(None)
        entries = feed_manager.feed_entries
        assert entries is not None
        assert len(entries) == 5
        assert len(generated_entity_external_ids) == 5
        assert len(updated_entity_external_ids) == 0
        assert len(removed_entity_external_ids) == 0

        feed_entry = entries["7C1469"]
        assert feed_entry.external_id == "7C1469"
        assert feed_entry.coordinates == (-33.7779, 151.1324)
        assert repr(feed_entry) == "<FeedEntry(id=7C1469)>"

        # Simulate an update with several changes.
        generated_entity_external_ids.clear()
        updated_entity_external_ids.clear()
        removed_entity_external_ids.clear()

        aresponses.add(
            "localhost:8754",
            "/flights.json",
            "get",
            aresponses.Response(
                text=load_fixture("fr24feed-flights-3.json"),
                content_type="application/json",
                status=200,
            ),
            match_querystring=True,
        )

        await feed_manager.update(None)
        entries = feed_manager.feed_entries
        assert entries is not None
        assert len(entries) == 5
        assert len(generated_entity_external_ids) == 1
        assert len(updated_entity_external_ids) == 4
        assert len(removed_entity_external_ids) == 1

        feed_entry = entries["7C1469"]
        assert feed_entry.external_id == "7C1469"
        assert feed_entry.coordinates == (-33.8880, 151.2435)

        # Simulate an update with no data.
        generated_entity_external_ids.clear()
        updated_entity_external_ids.clear()
        removed_entity_external_ids.clear()

        aresponses.add(
            "localhost:8754",
            "/flights.json",
            "get",
            aresponses.Response(text="ERROR", status=500),
            match_querystring=True,
        )

        await feed_manager.update(None)
        entries = feed_manager.feed_entries

        assert len(entries) == 0
        assert len(generated_entity_external_ids) == 0
        assert len(updated_entity_external_ids) == 0
        assert len(removed_entity_external_ids) == 5


def test_entry_without_data():
    """Test simple entry without data."""
    entry = FeedEntry(None, None)
    assert entry.coordinates is None
    assert entry.external_id is None
    assert entry.altitude is None
    assert entry.callsign is None
    assert entry.speed is None
    assert entry.track is None
    assert entry.squawk is None
    assert entry.vert_rate is None
    assert entry.updated is None

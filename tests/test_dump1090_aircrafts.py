"""Test for the Dump1090 Aircrafts feed."""
import asyncio
import datetime

import aiohttp
import pytest

from flightradar_client.consts import UPDATE_ERROR, UPDATE_OK
from flightradar_client.dump1090_aircrafts import (
    Dump1090AircraftsFeed,
    Dump1090AircraftsFeedAggregator,
    Dump1090AircraftsFeedManager,
)
from flightradar_client.feed_entry import FeedEntry
from tests.utils import load_fixture


@pytest.mark.asyncio
async def test_update_ok(aresponses, event_loop):
    """Test updating feed is ok."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8888",
        "/data/aircraft.json",
        "get",
        aresponses.Response(
            text=load_fixture("dump1090-aircrafts-1.json"),
            content_type="application/json",
            status=200,
        ),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = Dump1090AircraftsFeed(home_coordinates, websession)
        assert (
            repr(feed) == "<Dump1090AircraftsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8888/data/"
            "aircraft.json, "
            "radius=None)>"
        )
        status, entries = await feed.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 4

        feed_entry = entries["7c6d9a"]
        assert feed_entry.external_id == "7c6d9a"
        assert feed_entry.coordinates == (-34.234888, 150.533009)
        assert feed_entry.distance_to_home == pytest.approx(362.4, 0.1)
        assert feed_entry.altitude == 13075
        assert feed_entry.callsign == "QLK231D"
        assert feed_entry.updated == datetime.datetime(
            2018, 10, 26, 7, 35, 51, 400000, tzinfo=datetime.timezone.utc
        )
        assert feed_entry.speed == 357
        assert feed_entry.track == 61
        assert feed_entry.squawk == "7201"
        assert feed_entry.vert_rate == -1600

        assert repr(feed_entry) == "<FeedEntry(id=7c6d9a)>"


@pytest.mark.asyncio
async def test_update_ok_filter_radius(aresponses, event_loop):
    """Test updating feed is ok with filter radius."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8888",
        "/data/aircraft.json",
        "get",
        aresponses.Response(
            text=load_fixture("dump1090-aircrafts-1.json"),
            content_type="application/json",
            status=200,
        ),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = Dump1090AircraftsFeed(home_coordinates, websession, filter_radius=300)
        assert (
            repr(feed) == "<Dump1090AircraftsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8888/data/"
            "aircraft.json, "
            "radius=300)>"
        )
        status, entries = await feed.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 1


@pytest.mark.asyncio
async def test_update_error(aresponses, event_loop):
    """Test updating feed results in error."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8888",
        "/data/aircraft.json",
        "get",
        aresponses.Response(text="ERROR", status=500),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = Dump1090AircraftsFeed(home_coordinates, websession)
        status, entries = await feed.update()
        assert status == UPDATE_ERROR
        assert entries is None


@pytest.mark.asyncio
async def test_update_with_client_error(aresponses, event_loop):
    """Test updating feed raises exception."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8888",
        "/data/aircraft.json",
        "get",
        aiohttp.ClientError(),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = Dump1090AircraftsFeed(home_coordinates, websession)
        status, entries = await feed.update()
        assert status == UPDATE_ERROR
        assert entries is None


@pytest.mark.asyncio
async def test_update_with_timeout_error(aresponses, event_loop):
    """Test updating feed raises exception."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8888",
        "/data/aircraft.json",
        "get",
        asyncio.TimeoutError(),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed = Dump1090AircraftsFeed(home_coordinates, websession)
        status, entries = await feed.update()
        assert status == UPDATE_ERROR
        assert entries is None


@pytest.mark.asyncio
async def test_feed_aggregator(aresponses, event_loop):
    """Test updating feed through feed aggregator."""
    home_coordinates = (-31.0, 151.0)

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed_aggregator = Dump1090AircraftsFeedAggregator(home_coordinates, websession)
        assert (
            repr(feed_aggregator) == "<Dump1090AircraftsFeed"
            "Aggregator"
            "(feed=<Dump1090AircraftsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8888/"
            "data/aircraft.json, "
            "radius=None)>)>"
        )

        # Update 1
        aresponses.add(
            "localhost:8888",
            "/data/aircraft.json",
            "get",
            aresponses.Response(
                text=load_fixture("dump1090-aircrafts-1.json"),
                content_type="application/json",
                status=200,
            ),
            match_querystring=True,
        )
        status, entries = await feed_aggregator.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 4

        feed_entry = entries["7c6b28"]
        assert feed_entry.external_id == "7c6b28"
        assert feed_entry.coordinates == (-32.819840, 151.124735)
        assert feed_entry.altitude == 26000
        assert feed_entry.callsign == "JST423"

        assert repr(feed_entry) == "<FeedEntry(id=7c6b28)>"

        # Update 2
        aresponses.add(
            "localhost:8888",
            "/data/aircraft.json",
            "get",
            aresponses.Response(
                text=load_fixture("dump1090-aircrafts-2.json"),
                content_type="application/json",
                status=200,
            ),
            match_querystring=True,
        )
        status, entries = await feed_aggregator.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 5

        feed_entry = entries["7c6b28"]
        assert feed_entry.external_id == "7c6b28"
        assert feed_entry.coordinates == (-32.819840, 151.124735)
        assert feed_entry.altitude == 26000
        assert feed_entry.callsign == "JST423"


@pytest.mark.asyncio
async def test_feed_aggregator_filter_radius(aresponses, event_loop):
    """Test updating feed is ok with filter radius."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8888",
        "/data/aircraft.json",
        "get",
        aresponses.Response(
            text=load_fixture("dump1090-aircrafts-1.json"),
            content_type="application/json",
            status=200,
        ),
        match_querystring=True,
    )

    async with aiohttp.ClientSession(loop=event_loop) as websession:
        feed_aggregator = Dump1090AircraftsFeedAggregator(
            home_coordinates, websession, filter_radius=300
        )
        assert (
            repr(feed_aggregator) == "<Dump1090AircraftsFeed"
            "Aggregator"
            "(feed=<Dump1090AircraftsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8888/"
            "data/aircraft.json, "
            "radius=300)>)>"
        )

        status, entries = await feed_aggregator.update()
        assert status == UPDATE_OK
        assert entries is not None
        assert len(entries) == 1


@pytest.mark.asyncio
async def test_feed_manager(aresponses, event_loop):
    """Test the feed manager."""
    home_coordinates = (-31.0, 151.0)
    aresponses.add(
        "localhost:8888",
        "/data/aircraft.json",
        "get",
        aresponses.Response(
            text=load_fixture("dump1090-aircrafts-1.json"),
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
        feed_manager = Dump1090AircraftsFeedManager(
            _generate_entity,
            _update_entity,
            _remove_entity,
            home_coordinates,
            websession,
        )
        assert (
            repr(feed_manager) == "<Dump1090AircraftsFeedManager("
            "feed="
            "<Dump1090AircraftsFeedAggregator"
            "(feed=<Dump1090AircraftsFeed("
            "home=(-31.0, 151.0), "
            "url=http://localhost:8888/"
            "data/aircraft.json, "
            "radius=None)>)>)>"
        )
        await feed_manager.update(None)
        entries = feed_manager.feed_entries
        assert entries is not None
        assert len(entries) == 4
        assert len(generated_entity_external_ids) == 4
        assert len(updated_entity_external_ids) == 0
        assert len(removed_entity_external_ids) == 0


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

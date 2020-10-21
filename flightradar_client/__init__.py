"""
Local Flights Feeds.

Format-independent base classes for flights feeds.
"""
import aiohttp
import async_timeout
import asyncio
import datetime

from typing import Optional

import logging
from haversine import haversine

from flightradar_client.consts import UPDATE_OK, UPDATE_ERROR, \
    ATTR_LATITUDE, ATTR_LONGITUDE, ATTR_MODE_S, ATTR_ALTITUDE, \
    ATTR_CALLSIGN, ATTR_SPEED, ATTR_TRACK, ATTR_SQUAWK, ATTR_VERT_RATE, \
    ATTR_UPDATED, INVALID_COORDINATES, NONE_COORDINATES
from flightradar_client.exceptions import FlightradarException
from flightradar_client.statistics import StatisticsData

_LOGGER = logging.getLogger(__name__)


class Feed:
    """Data format independent feed."""

    def __init__(self, home_coordinates, session, loop=None,
                 apply_filters=True, filter_radius=None, url=None,
                 hostname=None, port=None):
        """Initialise feed."""
        self._home_coordinates = home_coordinates
        self._apply_filters = apply_filters
        self._filter_radius = filter_radius
        if session is None:
            raise FlightradarException("Session must not be None")
        self._session = session
        self._loop = loop
        if url:
            self._url = url
        else:
            self._url = self._create_url(hostname, port)

    def __repr__(self):
        """Return string representation of this feed."""
        return '<{}(home={}, url={}, radius={})>'.format(
            self.__class__.__name__, self._home_coordinates, self._url,
            self._filter_radius)

    def _create_url(self, hostname, port):
        """Generate the url to retrieve data from."""
        pass

    def _new_entry(self, home_coordinates, data):
        """Generate a new entry."""
        pass

    def _parse(self, json_string):
        """Parse the provided JSON data."""
        pass

    async def update(self):
        """Update from external source and return filtered entries."""
        status, data = await self._fetch()
        if status == UPDATE_OK:
            if data:
                feed_entries = []
                # Extract data from feed entries.
                for entry in data:
                    # Generate proper data objects.
                    feed_entries.append(self._new_entry(
                        self._home_coordinates, entry))
                filtered_entries = self._filter_entries(feed_entries)
                # Rebuild the entries and use external id as key.
                result_entries = {entry.external_id: entry
                                  for entry in filtered_entries}
                return UPDATE_OK, result_entries
            else:
                # Should not happen.
                return UPDATE_OK, None
        else:
            # Error happened while fetching the feed.
            return UPDATE_ERROR, None

    async def _fetch(self):
        """Fetch JSON data from external source."""
        try:
            async with async_timeout.timeout(10, loop=self._loop):
                response = await self._session.get(self._url)
                # Raise error if status >= 400.
                response.raise_for_status()
                data = await response.json()
                entries = self._parse(data)
                return UPDATE_OK, entries
        except aiohttp.ClientError as client_error:
            _LOGGER.warning("Fetching data from %s failed with %s",
                            self._url, client_error)
            return UPDATE_ERROR, None
        except asyncio.TimeoutError as timeout_error:
            _LOGGER.warning("Fetching data from %s failed with %s",
                            self._url, timeout_error)
            return UPDATE_ERROR, None

    def _filter_entries(self, entries):
        """Filter the provided entries."""
        filtered_entries = entries
        if self._apply_filters:
            # Always remove entries without coordinates.
            filtered_entries = list(
                filter(lambda entry:
                       (entry.coordinates is not None) and
                       (entry.coordinates != (None, None)),
                       filtered_entries))
            # Always remove entries on the ground (altitude: 0).
            filtered_entries = list(
                filter(lambda entry:
                       entry.altitude > 0,
                       filtered_entries))
            # Filter by distance.
            if self._filter_radius:
                filtered_entries = list(
                    filter(lambda entry:
                           entry.distance_to_home <= self._filter_radius,
                           filtered_entries))
        return filtered_entries


class FeedEntry:
    """Feed entry class."""

    def __init__(self, home_coordinates, data):
        """Initialise this feed entry."""
        self._home_coordinates = home_coordinates
        self._data = data
        self._statistics = None

    def __repr__(self):
        """Return string representation of this entry."""
        return '<{}(id={})>'.format(self.__class__.__name__, self.external_id)

    def override(self, key, value):
        """Override value in original data."""
        if self._data:
            self._data[key] = value

    @property
    def coordinates(self):
        """Return the coordinates of this entry."""
        if self._data:
            coordinates = (self._data[ATTR_LATITUDE], self._data[
                ATTR_LONGITUDE])
            return coordinates
        return None

    @property
    def distance_to_home(self):
        """Return the distance in km of this entry to the home coordinates."""
        return haversine(self._home_coordinates, self.coordinates)

    @property
    def external_id(self) -> Optional[str]:
        """Return the external id of this entry."""
        if self._data:
            return self._data[ATTR_MODE_S]
        return None

    @property
    def altitude(self) -> Optional[int]:
        """Return the altitude of this entry."""
        if self._data:
            altitude = self._data[ATTR_ALTITUDE]
            if altitude == 'ground':
                altitude = 0
            return altitude
        return None

    @property
    def callsign(self) -> Optional[str]:
        """Return the callsign of this entry."""
        if self._data:
            callsign = self._data[ATTR_CALLSIGN]
            if callsign:
                callsign = callsign.strip()
            return callsign
        return None

    @property
    def speed(self) -> Optional[int]:
        """Return the speed of this entry."""
        if self._data:
            return self._data[ATTR_SPEED]
        return None

    @property
    def track(self) -> Optional[int]:
        """Return the track of this entry."""
        if self._data:
            return self._data[ATTR_TRACK]
        return None

    @property
    def squawk(self) -> Optional[str]:
        """Return the squawk of this entry."""
        if self._data:
            return self._data[ATTR_SQUAWK]
        return None

    @property
    def vert_rate(self) -> Optional[int]:
        """Return the vertical rate of this entry."""
        if self._data:
            return self._data[ATTR_VERT_RATE]
        return None

    @property
    def updated(self) -> datetime:
        """Return the updated timestamp of this entry."""
        if self._data:
            updated = self._data[ATTR_UPDATED]
            if updated:
                # Parse the date. Timestamp in microseconds from unix epoch.
                return datetime.datetime.fromtimestamp(
                    updated, tz=datetime.timezone.utc)
        return None

    @property
    def statistics(self) -> Optional[StatisticsData]:
        """Return statistics data for this entry."""
        return self._statistics

    @statistics.setter
    def statistics(self, value):
        """Set statistics value."""
        self._statistics = value

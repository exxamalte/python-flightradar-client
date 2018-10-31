"""
Local Flightradar24 Flights Feed.

Fetches JSON feed from a local Flightradar24 flights feed.
"""
import collections
import datetime
import json
import logging
from haversine import haversine
from typing import Optional

from flightradar24_client import Feed, DEFAULT_HOSTNAME, DEFAULT_PORT
from flightradar24_client.consts import UPDATE_OK, ATTR_VERT_RATE, ATTR_SQUAWK, \
    ATTR_TRACK, ATTR_UPDATED, ATTR_SPEED, ATTR_CALLSIGN, ATTR_ALTITUDE, \
    ATTR_MODE_S, ATTR_LONGITUDE, ATTR_LATITUDE

_LOGGER = logging.getLogger(__name__)

DEFAULT_AGGREGATOR_STACK_SIZE = 10

URL_TEMPLATE = "http://{}:{}/flights.json"


class Flightradar24FlightsFeedAggregator:
    """Aggregates date received from the feed over a period of time."""

    def __init__(self, home_coordinates, filter_radius=None,
                 hostname=DEFAULT_HOSTNAME, port=DEFAULT_PORT):
        """Initialise feed aggregator."""
        self._feed = Flightradar24FlightsFeed(home_coordinates, filter_radius,
                                              hostname, port)
        self._stack = collections.deque(DEFAULT_AGGREGATOR_STACK_SIZE * [[]],
                                        DEFAULT_AGGREGATOR_STACK_SIZE)
        self._callsigns = {}

    def __repr__(self):
        """Return string representation of this feed aggregator."""
        return '<{}(feed={})>'.format(
            self.__class__.__name__, self._feed)

    def update(self):
        """Update from external source, aggregate with previous data and
        return filtered entries."""
        status, data = self._feed.update()
        if status == UPDATE_OK:
            self._stack.pop()
            self._stack.appendleft(data)
        # Fill in some gaps in data received.
        for key in data:
            # Keep record of callsigns.
            if key not in self._callsigns and data[key].callsign:
                self._callsigns[key] = data[key].callsign
            # Fill in callsign from previous update if currently missing.
            if not data[key].callsign and key in self._callsigns:
                data[key].override(ATTR_CALLSIGN, self._callsigns[key])
        _LOGGER.debug("Callsigns = %s", self._callsigns)
        return status, data


class Flightradar24FlightsFeed(Feed):
    """Flightradar24 Flights Feed."""

    def _url(self, hostname, port):
        """Generate the url to retrieve data from."""
        return URL_TEMPLATE.format(hostname, port)

    def _new_entry(self, home_coordinates, feed_data):
        """Generate a new entry."""
        return Flightradar24FeedEntry(home_coordinates, feed_data)

    def _parse(self, json_string):
        """Parse the provided JSON data."""
        result = []
        parsed_json = json.loads(json_string)
        for key in parsed_json:
            data_entry = parsed_json[key]
            result.append({
                ATTR_MODE_S: data_entry[0],
                ATTR_LATITUDE: data_entry[1],
                ATTR_LONGITUDE: data_entry[2],
                ATTR_TRACK: data_entry[3],
                ATTR_ALTITUDE: data_entry[4],
                ATTR_SPEED: data_entry[5],
                ATTR_SQUAWK: data_entry[6],
                ATTR_UPDATED: data_entry[10],
                ATTR_VERT_RATE: data_entry[15],
                ATTR_CALLSIGN: data_entry[16],
            })
        return result


class Flightradar24FeedEntry:
    """Feed entry class."""

    def __init__(self, home_coordinates, data):
        """Initialise this feed entry."""
        self._home_coordinates = home_coordinates
        self._data = data

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
    def altitude(self) -> Optional[str]:
        """Return the altitude of this entry."""
        if self._data:
            return self._data[ATTR_ALTITUDE]
        return None

    @property
    def callsign(self) -> Optional[str]:
        """Return the callsign of this entry."""
        if self._data:
            return self._data[ATTR_CALLSIGN]
        return None

    @property
    def speed(self) -> Optional[str]:
        """Return the speed of this entry."""
        if self._data:
            return self._data[ATTR_SPEED]
        return None

    @property
    def track(self) -> Optional[str]:
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
    def vert_rate(self) -> Optional[str]:
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

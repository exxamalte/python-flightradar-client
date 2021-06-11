"""
Local Dump1090 Aircrafts Feed.

Fetches JSON feed from a local Dump1090 aircrafts feed.
"""
import logging

from .consts import (
    ATTR_ALTITUDE,
    ATTR_CALLSIGN,
    ATTR_FLIGHT,
    ATTR_HEX,
    ATTR_LAT,
    ATTR_LATITUDE,
    ATTR_LON,
    ATTR_LONGITUDE,
    ATTR_MODE_S,
    ATTR_SPEED,
    ATTR_SQUAWK,
    ATTR_TRACK,
    ATTR_UPDATED,
    ATTR_VERT_RATE,
)
from .feed import Feed
from .feed_aggregator import FeedAggregator
from .feed_entry import FeedEntry
from .feed_manager import FeedManagerBase

_LOGGER = logging.getLogger(__name__)

DEFAULT_HOSTNAME = "localhost"
DEFAULT_PORT = 8888

URL_TEMPLATE = "http://{}:{}/data/aircraft.json"


class Dump1090AircraftsFeedManager(FeedManagerBase):
    """Feed Manager for Dump1090 Aircrafts feed."""

    def __init__(
        self,
        generate_callback,
        update_callback,
        remove_callback,
        coordinates,
        session,
        loop=None,
        filter_radius=None,
        url=None,
        hostname=DEFAULT_HOSTNAME,
        port=DEFAULT_PORT,
    ):
        """Initialize the NSW Rural Fire Services Feed Manager."""
        feed = Dump1090AircraftsFeedAggregator(
            coordinates,
            session,
            loop=loop,
            filter_radius=filter_radius,
            url=url,
            hostname=hostname,
            port=port,
        )
        super().__init__(feed, generate_callback, update_callback, remove_callback)


class Dump1090AircraftsFeedAggregator(FeedAggregator):
    """Aggregates date received from the feed over a period of time."""

    def __init__(
        self,
        home_coordinates,
        session,
        loop=None,
        filter_radius=None,
        url=None,
        hostname=DEFAULT_HOSTNAME,
        port=DEFAULT_PORT,
    ):
        """Initialise feed aggregator."""
        super().__init__(filter_radius)
        self._feed = Dump1090AircraftsFeed(
            home_coordinates, session, loop, False, filter_radius, url, hostname, port
        )

    @property
    def feed(self):
        """Return the external feed access."""
        return self._feed


class Dump1090AircraftsFeed(Feed):
    """Dump1090 Aircrafts Feed."""

    def __init__(
        self,
        home_coordinates,
        session,
        loop=None,
        apply_filters=True,
        filter_radius=None,
        url=None,
        hostname=DEFAULT_HOSTNAME,
        port=DEFAULT_PORT,
    ):
        super().__init__(
            home_coordinates,
            session,
            loop,
            apply_filters,
            filter_radius,
            url,
            hostname,
            port,
        )

    def _create_url(self, hostname, port):
        """Generate the url to retrieve data from."""
        return URL_TEMPLATE.format(hostname, port)

    def _new_entry(self, home_coordinates, feed_data):
        """Generate a new entry."""
        return FeedEntry(home_coordinates, feed_data)

    def _parse(self, parsed_json):
        """Parse the provided JSON data."""
        result = []
        timestamp = None if "now" not in parsed_json else parsed_json["now"]
        if "aircraft" in parsed_json:
            aircrafts = parsed_json["aircraft"]
            for entry in aircrafts:
                result.append(
                    {
                        ATTR_MODE_S: entry.get(ATTR_HEX, None),
                        ATTR_LATITUDE: entry.get(ATTR_LAT, None),
                        ATTR_LONGITUDE: entry.get(ATTR_LON, None),
                        ATTR_TRACK: entry.get(ATTR_TRACK, None),
                        ATTR_ALTITUDE: entry.get(ATTR_ALTITUDE, None),
                        ATTR_SPEED: entry.get(ATTR_SPEED, None),
                        ATTR_SQUAWK: entry.get(ATTR_SQUAWK, None),
                        ATTR_UPDATED: timestamp,
                        ATTR_VERT_RATE: entry.get(ATTR_VERT_RATE, None),
                        ATTR_CALLSIGN: entry.get(ATTR_FLIGHT, None),
                    }
                )
        _LOGGER.debug("Parser result = %s", result)
        return result

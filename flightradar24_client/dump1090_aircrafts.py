"""
Local Dump1090 Aircrafts Feed.

Fetches JSON feed from a local Dump1090 aircrafts feed.
"""
import logging

from flightradar24_client import Feed, FeedEntry, FeedAggregator
from flightradar24_client.consts import ATTR_VERT_RATE, ATTR_SQUAWK, \
    ATTR_TRACK, ATTR_UPDATED, ATTR_SPEED, ATTR_CALLSIGN, ATTR_ALTITUDE, \
    ATTR_MODE_S, ATTR_LONGITUDE, ATTR_LATITUDE, ATTR_LON, ATTR_LAT, ATTR_HEX, \
    ATTR_FLIGHT

_LOGGER = logging.getLogger(__name__)

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_PORT = 8888

URL_TEMPLATE = "http://{}:{}/data/aircraft.json"


class Dump1090AircraftsFeedAggregator(FeedAggregator):
    """Aggregates date received from the feed over a period of time."""

    def __init__(self, home_coordinates, filter_radius=None, url=None,
                 hostname=DEFAULT_HOSTNAME, port=DEFAULT_PORT, loop=None,
                 session=None):
        """Initialise feed aggregator."""
        super().__init__(filter_radius)
        self._feed = Dump1090AircraftsFeed(home_coordinates, False,
                                           filter_radius, url, hostname, port,
                                           loop, session)

    @property
    def feed(self):
        """Return the external feed access."""
        return self._feed


class Dump1090AircraftsFeed(Feed):
    """Dump1090 Aircrafts Feed."""

    def __init__(self, home_coordinates, apply_filters=True,
                 filter_radius=None, url=None, hostname=DEFAULT_HOSTNAME,
                 port=DEFAULT_PORT, loop=None, session=None):
        super().__init__(home_coordinates, apply_filters, filter_radius, url,
                         hostname, port, loop, session)

    def _create_url(self, hostname, port):
        """Generate the url to retrieve data from."""
        return URL_TEMPLATE.format(hostname, port)

    def _new_entry(self, home_coordinates, feed_data):
        """Generate a new entry."""
        return FeedEntry(home_coordinates, feed_data)

    def _parse(self, parsed_json):
        """Parse the provided JSON data."""
        result = []
        timestamp = None if 'now' not in parsed_json else parsed_json['now']
        if 'aircraft' in parsed_json:
            aircrafts = parsed_json['aircraft']
            for entry in aircrafts:
                result.append({
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
                })
        _LOGGER.debug("Parser result = %s", result)
        return result

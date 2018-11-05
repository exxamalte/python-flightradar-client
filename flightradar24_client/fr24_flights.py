"""
Local Flightradar24 Flights Feed.

Fetches JSON feed from a local Flightradar24 flights feed.
"""
import collections
import json
import logging

from flightradar24_client import Feed, FeedEntry
from flightradar24_client.utils import FixedSizeDict
from flightradar24_client.consts import UPDATE_OK, ATTR_VERT_RATE, \
    ATTR_SQUAWK, ATTR_TRACK, ATTR_UPDATED, ATTR_SPEED, ATTR_CALLSIGN, \
    ATTR_ALTITUDE, ATTR_MODE_S, ATTR_LONGITUDE, ATTR_LATITUDE

_LOGGER = logging.getLogger(__name__)

DEFAULT_AGGREGATOR_STACK_SIZE = 10
DEFAULT_HOSTNAME = 'localhost'
DEFAULT_PORT = 8754

URL_TEMPLATE = "http://{}:{}/flights.json"


class Flightradar24FlightsFeedAggregator:
    """Aggregates date received from the feed over a period of time."""

    def __init__(self, home_coordinates, filter_radius=None,
                 hostname=DEFAULT_HOSTNAME, port=DEFAULT_PORT):
        """Initialise feed aggregator."""
        self._feed = Flightradar24FlightsFeed(home_coordinates, False,
                                              filter_radius, hostname, port)
        self._filter_radius = filter_radius
        self._stack = collections.deque(DEFAULT_AGGREGATOR_STACK_SIZE * [[]],
                                        DEFAULT_AGGREGATOR_STACK_SIZE)
        self._callsigns = FixedSizeDict(max=500)
        self._altitudes = FixedSizeDict(max=500)

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
            # Keep record of altitudes.
            if key not in self._altitudes and data[key].altitude:
                self._altitudes[key] = data[key].altitude
            # Update altitude.
            # TODO
        _LOGGER.debug("Callsigns = %s", self._callsigns)
        _LOGGER.debug("Altitudes = %s", self._altitudes)
        # Filter.
        filtered_entries = self._filter_entries(data.values())
        # Rebuild the entries and use external id as key.
        result_entries = {entry.external_id: entry
                          for entry in filtered_entries}
        return status, result_entries

    def _filter_entries(self, entries):
        """Filter the provided entries."""
        filtered_entries = entries
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


class Flightradar24FlightsFeed(Feed):
    """Flightradar24 Flights Feed."""

    def __init__(self, home_coordinates, apply_filters=True,
                 filter_radius=None, hostname=DEFAULT_HOSTNAME,
                 port=DEFAULT_PORT):
        super().__init__(home_coordinates, apply_filters, filter_radius,
                         hostname, port)

    def _create_url(self, hostname, port):
        """Generate the url to retrieve data from."""
        return URL_TEMPLATE.format(hostname, port)

    def _new_entry(self, home_coordinates, feed_data):
        """Generate a new entry."""
        return FeedEntry(home_coordinates, feed_data)

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

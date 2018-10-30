"""flightradar24-client library."""
import logging
import requests
from json import JSONDecodeError

from flightradar24_client.consts import UPDATE_OK, UPDATE_ERROR

_LOGGER = logging.getLogger(__name__)

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_PORT = 8754


class Feed:
    """Data format independent feed."""

    def __init__(self, home_coordinates, filter_radius=None,
                 hostname=DEFAULT_HOSTNAME, port=DEFAULT_PORT):
        """Initialise feed."""
        self._home_coordinates = home_coordinates
        self._filter_radius = filter_radius
        self._url = self._url(hostname, port)
        self._request = requests.Request(method="GET", url=self._url).prepare()

    def __repr__(self):
        """Return string representation of this feed."""
        return '<{}(home={}, url={}, radius={})>'.format(
            self.__class__.__name__, self._home_coordinates, self._url,
            self._filter_radius)

    def _url(self, hostname, port):
        """Generate the url to retrieve data from."""
        pass

    def _new_entry(self, home_coordinates, data):
        """Generate a new entry."""
        pass

    def _parse(self, json_string):
        """Parse the provided JSON data."""
        pass

    def update(self):
        """Update from external source and return filtered entries."""
        status, data = self._fetch()
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

    def _fetch(self):
        """Fetch JSON data from external source."""
        try:
            with requests.Session() as session:
                response = session.send(self._request, timeout=10)
            if response.ok:
                entries = self._parse(response.text)
                return UPDATE_OK, entries
            else:
                _LOGGER.warning(
                    "Fetching data from %s failed with status %s",
                    self._request.url, response.status_code)
                return UPDATE_ERROR, None
        except requests.exceptions.RequestException as request_ex:
            _LOGGER.warning("Fetching data from %s failed with %s",
                            self._request.url, request_ex)
            return UPDATE_ERROR, None
        except JSONDecodeError as decode_ex:
            _LOGGER.warning("Unable to parse JSON from %s: %s",
                            self._request.url, decode_ex)
            return UPDATE_ERROR, None

    def _filter_entries(self, entries):
        """Filter the provided entries."""
        filtered_entries = entries
        # Always remove entries without coordinates.
        filtered_entries = list(
            filter(lambda entry:
                   entry.coordinates is not None,
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

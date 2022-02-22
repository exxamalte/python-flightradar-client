"""
Local Flightradar Flights Feed.

Fetches JSON feed from a local Flightradar flights feed.
"""
import logging
from typing import Awaitable, Callable, Dict, List, Tuple

from aiohttp import ClientSession

from .consts import (
    ATTR_ALTITUDE,
    ATTR_CALLSIGN,
    ATTR_LATITUDE,
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
DEFAULT_PORT = 8754

URL_TEMPLATE = "http://{}:{}/flights.json"


class FlightradarFlightsFeedManager(FeedManagerBase):
    """Feed Manager for Flightradar Flights feed."""

    def __init__(
        self,
        generate_callback: Callable[[str], Awaitable[None]],
        update_callback: Callable[[str], Awaitable[None]],
        remove_callback: Callable[[str], Awaitable[None]],
        coordinates: Tuple[float, float],
        websession: ClientSession,
        filter_radius: float = None,
        url: str = None,
        hostname: str = DEFAULT_HOSTNAME,
        port: int = DEFAULT_PORT,
    ) -> None:
        """Initialize the NSW Rural Fire Services Feed Manager."""
        feed = FlightradarFlightsFeedAggregator(
            coordinates,
            websession,
            filter_radius=filter_radius,
            url=url,
            hostname=hostname,
            port=port,
        )
        super().__init__(feed, generate_callback, update_callback, remove_callback)


class FlightradarFlightsFeedAggregator(FeedAggregator):
    """Aggregates date received from the feed over a period of time."""

    def __init__(
        self,
        home_coordinates: Tuple[float, float],
        websession: ClientSession,
        filter_radius: float = None,
        url: str = None,
        hostname: str = DEFAULT_HOSTNAME,
        port: int = DEFAULT_PORT,
    ) -> None:
        """Initialise feed aggregator."""
        super().__init__(filter_radius)
        self._feed = FlightradarFlightsFeed(
            home_coordinates,
            websession,
            False,
            filter_radius,
            url,
            hostname,
            port,
        )

    @property
    def feed(self) -> Feed:
        """Return the external feed access."""
        return self._feed


class FlightradarFlightsFeed(Feed):
    """Flightradar Flights Feed."""

    def __init__(
        self,
        home_coordinates: Tuple[float, float],
        websession: ClientSession,
        apply_filters: bool = True,
        filter_radius: float = None,
        url: str = None,
        hostname: str = DEFAULT_HOSTNAME,
        port: int = DEFAULT_PORT,
    ) -> None:
        super().__init__(
            home_coordinates,
            websession,
            apply_filters,
            filter_radius,
            url,
            hostname,
            port,
        )

    def _create_url(self, hostname: str, port: int) -> str:
        """Generate the url to retrieve data from."""
        return URL_TEMPLATE.format(hostname, port)

    def _new_entry(
        self, home_coordinates: Tuple[float, float], feed_data: Dict
    ) -> FeedEntry:
        """Generate a new entry."""
        return FeedEntry(home_coordinates, feed_data)

    def _parse(self, parsed_json: Dict) -> List[Dict]:
        """Parse the provided JSON data."""
        result = []
        for key in parsed_json:
            data_entry = parsed_json[key]
            result.append(
                {
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
                }
            )
        _LOGGER.debug("Parser result = %s", result)
        return result

"""Feed."""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple

import aiohttp
from aiohttp import ClientSession, client_exceptions

from .consts import UPDATE_ERROR, UPDATE_OK
from .exceptions import FlightradarException
from .feed_entry import FeedEntry

_LOGGER = logging.getLogger(__name__)


class Feed:
    """Data format independent feed."""

    def __init__(
        self,
        home_coordinates: Tuple[float, float],
        websession: ClientSession,
        apply_filters=True,
        filter_radius=None,
        url=None,
        hostname=None,
        port=None,
    ) -> None:
        """Initialise feed."""
        self._home_coordinates = home_coordinates
        self._apply_filters = apply_filters
        self._filter_radius = filter_radius
        if websession is None:
            raise FlightradarException("Session must not be None")
        self._websession = websession
        if url:
            self._url = url
        else:
            self._url = self._create_url(hostname, port)

    def __repr__(self) -> str:
        """Return string representation of this feed."""
        return "<{}(home={}, url={}, radius={})>".format(
            self.__class__.__name__,
            self._home_coordinates,
            self._url,
            self._filter_radius,
        )

    def _create_url(self, hostname, port) -> str:
        """Generate the url to retrieve data from."""
        pass

    def _new_entry(self, home_coordinates: Tuple[float, float], data) -> FeedEntry:
        """Generate a new entry."""
        pass

    def _parse(self, parsed_json: Dict) -> List[Dict]:
        """Parse the provided JSON data."""
        pass

    async def update(self) -> Tuple[str, Optional[Dict[str, FeedEntry]]]:
        """Update from external source and return filtered entries."""
        status, data = await self._fetch()
        if status == UPDATE_OK:
            if data:
                feed_entries = []
                # Extract data from feed entries.
                for entry in data:
                    # Generate proper data objects.
                    feed_entries.append(self._new_entry(self._home_coordinates, entry))
                filtered_entries = self._filter_entries(feed_entries)
                # Rebuild the entries and use external id as key.
                result_entries = {
                    entry.external_id: entry for entry in filtered_entries
                }
                return UPDATE_OK, result_entries
            else:
                # Should not happen.
                return UPDATE_OK, None
        else:
            # Error happened while fetching the feed.
            return UPDATE_ERROR, None

    async def _fetch(self) -> Tuple[str, Optional[List[Dict]]]:
        """Fetch JSON data from external source."""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with self._websession.request(
                "GET", self._url, timeout=timeout
            ) as response:
                try:
                    # Raise error if status >= 400.
                    response.raise_for_status()
                    data = await response.json()

                    entries = self._parse(data)
                    return UPDATE_OK, entries
                except client_exceptions.ClientError as client_error:
                    _LOGGER.warning(
                        "Fetching data from %s failed with %s", self._url, client_error
                    )
                    return UPDATE_ERROR, None
        except aiohttp.ClientError as client_error:
            _LOGGER.warning(
                "Fetching data from %s failed with %s", self._url, client_error
            )
            return UPDATE_ERROR, None
        except asyncio.TimeoutError as timeout_error:
            _LOGGER.warning(
                "Fetching data from %s failed with %s", self._url, timeout_error
            )
            return UPDATE_ERROR, None

    def _filter_entries(self, entries: List[FeedEntry]) -> List[FeedEntry]:
        """Filter the provided entries."""
        filtered_entries = entries
        if self._apply_filters:
            # Always remove entries without coordinates.
            filtered_entries = list(
                filter(
                    lambda entry: (entry.coordinates is not None)
                    and (entry.coordinates != (None, None)),
                    filtered_entries,
                )
            )
            # Always remove entries on the ground (altitude: 0).
            filtered_entries = list(
                filter(lambda entry: entry.altitude > 0, filtered_entries)
            )
            # Filter by distance.
            if self._filter_radius:
                filtered_entries = list(
                    filter(
                        lambda entry: entry.distance_to_home <= self._filter_radius,
                        filtered_entries,
                    )
                )
        return filtered_entries

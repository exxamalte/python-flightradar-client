"""Feed aggregator base class."""
import collections
import logging

from .consts import (
    ATTR_CALLSIGN,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    INVALID_COORDINATES,
    NONE_COORDINATES,
    UPDATE_OK,
)
from .statistics import Statistics
from .utils import FixedSizeDict

_LOGGER = logging.getLogger(__name__)

DEFAULT_AGGREGATOR_STACK_SIZE = 10
DEFAULT_CALLSIGNS_CACHE_SIZE = 250
DEFAULT_COORDINATES_CACHE_SIZE = 250


class FeedAggregator:
    """Aggregates date received from the feed over a period of time."""

    def __init__(self, filter_radius=None):
        """Initialise feed aggregator."""
        self._filter_radius = filter_radius
        self._stack = collections.deque(
            DEFAULT_AGGREGATOR_STACK_SIZE * [[]], DEFAULT_AGGREGATOR_STACK_SIZE
        )
        self._callsigns = FixedSizeDict(max=DEFAULT_CALLSIGNS_CACHE_SIZE)
        self._coordinates = FixedSizeDict(max=DEFAULT_COORDINATES_CACHE_SIZE)
        self._statistics = Statistics()

    def __repr__(self):
        """Return string representation of this feed aggregator."""
        return "<{}(feed={})>".format(self.__class__.__name__, self.feed)

    @property
    def feed(self):
        """Return the external feed access."""
        return None

    async def update(self):
        """Update from external source, aggregate with previous data and
        return filtered entries."""
        status, data = await self.feed.update()
        if status == UPDATE_OK:
            self._stack.pop()
            self._stack.appendleft(data)
        if data:
            # Fill in some gaps in data received.
            await self._update_cache(data)
            # Update statistics
            await self._statistics.retrieval_successful(data.keys())
            # Filter entries.
            filtered_entries = await self._filter_entries(data.values())
            # Insert statistics data.
            await self._insert_statistics_data(filtered_entries)
            # filtered_entries = self._insert_statistics_data(filtered_entries)
            # Rebuild the entries and use external id as key.
            result_entries = {entry.external_id: entry for entry in filtered_entries}
            return status, result_entries
        # Update statistics
        await self._statistics.retrieval_unsuccessful()
        return status, None

    async def _update_cache(self, data):
        for key in data:
            # Keep record of callsigns.
            if key not in self._callsigns and data[key].callsign:
                self._callsigns[key] = data[key].callsign
            # Fill in callsign from previous update if currently missing.
            if not data[key].callsign and key in self._callsigns:
                data[key].override(ATTR_CALLSIGN, self._callsigns[key])
            # Keep record of latest coordinates.
            # Here we are considering (lat=0, lon=0) as unwanted
            # coordinates, despite the fact that they are valid.
            # Typically, coordinates (0, 0) indicate that the correct
            # coordinates have not been received.
            if (
                data[key].coordinates
                and data[key].coordinates != INVALID_COORDINATES
                and data[key].coordinates != NONE_COORDINATES
            ):
                self._coordinates[key] = data[key].coordinates
            # Fill in missing coordinates.
            if (
                not data[key].coordinates
                or data[key].coordinates == INVALID_COORDINATES
                or data[key].coordinates == NONE_COORDINATES
            ) and key in self._coordinates:
                data[key].override(ATTR_LATITUDE, self._coordinates[key][0])
                data[key].override(ATTR_LONGITUDE, self._coordinates[key][1])
        _LOGGER.debug("Callsigns = %s", self._callsigns)
        _LOGGER.debug("Coordinates = %s", self._coordinates)

    async def _filter_entries(self, entries):
        """Filter the provided entries."""
        filtered_entries = entries
        # Always remove entries without coordinates.
        filtered_entries = list(
            filter(
                lambda entry: (entry.coordinates is not None)
                and (entry.coordinates != INVALID_COORDINATES)
                and (entry.coordinates != NONE_COORDINATES),
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

    async def _insert_statistics_data(self, entries):
        """Update current statistics data for each entry."""
        if entries:
            for entry in entries:
                statistics_entry = self._statistics.get(entry.external_id)
                if statistics_entry:
                    entry.statistics = statistics_entry

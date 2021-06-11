"""Feed Entry."""
import datetime
import logging
from typing import Optional

from haversine import haversine

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
from .statistics import StatisticsData

_LOGGER = logging.getLogger(__name__)


class FeedEntry:
    """Feed entry class."""

    def __init__(self, home_coordinates, data):
        """Initialise this feed entry."""
        self._home_coordinates = home_coordinates
        self._data = data
        self._statistics = None

    def __repr__(self):
        """Return string representation of this entry."""
        return "<{}(id={})>".format(self.__class__.__name__, self.external_id)

    def override(self, key, value):
        """Override value in original data."""
        if self._data:
            self._data[key] = value

    @property
    def coordinates(self):
        """Return the coordinates of this entry."""
        if self._data:
            coordinates = (self._data[ATTR_LATITUDE], self._data[ATTR_LONGITUDE])
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
            if altitude == "ground":
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
                    updated, tz=datetime.timezone.utc
                )
        return None

    @property
    def statistics(self) -> Optional[StatisticsData]:
        """Return statistics data for this entry."""
        return self._statistics

    @statistics.setter
    def statistics(self, value):
        """Set statistics value."""
        self._statistics = value

"""Feed statistics."""
from .utils import FixedSizeDict

DEFAULT_STATISTICS_ENTRY_SIZE = 250


class Statistics:
    """Statistics collector."""

    def __init__(self):
        """Initialise statistics."""
        self._entries = FixedSizeDict(max=DEFAULT_STATISTICS_ENTRY_SIZE)

    def __repr__(self):
        """Return string representation of the statistics."""
        return "<Statistics[{}]>".format(self._entries)

    def get(self, key):
        """Get entry for provided key."""
        if key and key in self._entries:
            return self._entries[key]
        return None

    async def retrieval_successful(self, updated_keys):
        """Record a successful retrieval."""
        # 1. Update existing entries.
        for key in self._entries:
            if key in updated_keys:
                self._entries[key].retrieval_successful()
            else:
                self._entries[key].retrieval_unsuccessful()
        # 2. Add new entries.
        for key in updated_keys:
            if key not in self._entries:
                self._entries[key] = StatisticsData(True)

    async def retrieval_unsuccessful(self):
        """Record an unsuccessful retrieval."""
        for key in self._entries:
            # Always increase counter for total number of retrievals.
            self._entries[key].retrieval_unsuccessful()


class StatisticsData:
    """Statistics data for a single feed entry."""

    def __init__(self, retrieval_successful):
        """Initialise statistics entry."""
        self._retrievals = 1 if retrieval_successful else 0
        self._total = 1

    def __repr__(self):
        """Return string representation of the statistics."""
        return "<StatisticsData({:.1%})>".format(self.success_ratio())

    def retrieval_successful(self):
        """Record a successful update."""
        self._retrievals = self._retrievals + 1
        self._total = self._total + 1

    def retrieval_unsuccessful(self):
        """Record an unsuccessful update."""
        self._total = self._total + 1

    def success_ratio(self):
        """Calculate success ratio."""
        if self._total == 0:
            return 0
        return self._retrievals / self._total

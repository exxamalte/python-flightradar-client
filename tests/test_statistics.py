"""Test for the statistics collector."""
import asynctest

from flightradar_client.statistics import Statistics, StatisticsData


class TestStatistics(asynctest.TestCase):
    """Test for the statistics collector."""

    async def test_basic_statistics(self):
        """Test some basic statistics behaviour."""
        statistics = Statistics()
        assert repr(statistics) == "<Statistics[FixedSizeDict()]>"

        value = statistics.get("non-existing")
        self.assertIsNone(value)

    async def test_basic_statistics_data(self):
        """Test some basic statistics data behaviour."""
        statistics_data = StatisticsData(False)
        assert repr(statistics_data) == "<StatisticsData(0.0%)>"
        statistics_data._total = 0
        assert repr(statistics_data) == "<StatisticsData(0.0%)>"
        # 1. successful update.
        statistics_data.update_successful()
        assert repr(statistics_data) == "<StatisticsData(100.0%)>"
        # 2. unsuccessful update.
        statistics_data.update_unsuccessful()
        assert repr(statistics_data) == "<StatisticsData(50.0%)>"

    async def test_update(self):
        """Test an update."""
        statistics = Statistics()
        KEYS = ["a", "b", "c"]
        # 1. successful update.
        await statistics.update_successful(KEYS)
        assert statistics.get("a").success_ratio() == 1.0
        # 2. successful update.
        await statistics.update_successful(KEYS)
        assert statistics.get("a").success_ratio() == 1.0
        # 3. unsuccessful update.
        await statistics.update_unsuccessful()
        self.assertAlmostEqual(statistics.get("a").success_ratio(), 0.666, 2)
        assert repr(statistics.get("a")) == "<StatisticsData(66.7%)>"

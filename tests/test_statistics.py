"""Test for the statistics collector."""
import pytest as pytest

from flightradar_client.statistics import Statistics, StatisticsData


@pytest.mark.asyncio
async def test_basic_statistics():
    """Test some basic statistics behaviour."""
    statistics = Statistics()
    assert repr(statistics) == "<Statistics[FixedSizeDict()]>"

    value = statistics.get("non-existing")
    assert value is None


@pytest.mark.asyncio
async def test_basic_statistics_data():
    """Test some basic statistics data behaviour."""
    statistics_data = StatisticsData(False)
    assert repr(statistics_data) == "<StatisticsData(0.0%)>"
    statistics_data._total = 0
    assert repr(statistics_data) == "<StatisticsData(0.0%)>"
    # 1. successful update.
    statistics_data.retrieval_successful()
    assert repr(statistics_data) == "<StatisticsData(100.0%)>"
    # 2. unsuccessful update.
    statistics_data.retrieval_unsuccessful()
    assert repr(statistics_data) == "<StatisticsData(50.0%)>"


@pytest.mark.asyncio
async def test_update():
    """Test an update."""
    statistics = Statistics()
    KEYS = ["a", "b", "c"]
    # 1. successful update.
    await statistics.retrieval_successful(KEYS)
    assert statistics.get("a").success_ratio() == 1.0
    # 2. successful update.
    await statistics.retrieval_successful(KEYS)
    assert statistics.get("a").success_ratio() == 1.0
    # 3. unsuccessful update.
    await statistics.retrieval_unsuccessful()
    assert round(abs(statistics.get("a").success_ratio() - 0.666), 2) == 0
    assert repr(statistics.get("a")) == "<StatisticsData(66.7%)>"

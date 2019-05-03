"""Test for the library utils."""
import unittest

from flightradar_client.utils import FixedSizeDict


class TestFixedSizeDict(unittest.TestCase):
    """Test the FixedSizeDict."""

    def test_dict(self):
        """Test general setup of fixed size dict."""
        test_dict = FixedSizeDict(max=2)

        test_dict['key1'] = 'value1'
        assert len(test_dict) == 1
        test_dict['key2'] = 'value2'
        assert len(test_dict) == 2
        test_dict['key3'] = 'value3'
        assert len(test_dict) == 2
        assert 'key1' not in test_dict

"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_gps_packet():
    """Sample GPS packet data for testing."""
    return {
        "vehicle_id": "BUS001",
        "latitude": 28.8053,
        "longitude": -96.9853,
        "speed": 25.5,
        "heading": 180.0
    }


@pytest.fixture
def sample_raw_packet():
    """Sample raw UDP packet for testing."""
    return b"BUS001,28.8053,-96.9853,25.5,180.0"

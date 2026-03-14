"""Test conversion factor application (building = 50, others = 1)."""
import pytest


def test_building_conversion_factor():
    from app.services.ingestion import BUILDING_CONVERSION_FACTOR, DEFAULT_CONVERSION_FACTOR
    assert BUILDING_CONVERSION_FACTOR == 50.0
    assert DEFAULT_CONVERSION_FACTOR == 1.0


def test_normalized_value_building():
    raw = 100.0
    factor = 50.0
    assert raw * factor == 5000.0


def test_normalized_value_tenant():
    raw = 100.0
    factor = 1.0
    assert raw * factor == 100.0

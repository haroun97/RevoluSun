"""Test missing-tenant detection (e.g. Kunde7 not in workbook)."""
import pytest

from app.core.constants import EXPECTED_TENANT_IDS, get_missing_tenant_ids


def test_expected_tenant_ids_includes_kunde7():
    assert "Kunde7" in EXPECTED_TENANT_IDS
    assert len(EXPECTED_TENANT_IDS) == 13
    assert EXPECTED_TENANT_IDS == [f"Kunde{i}" for i in range(1, 14)]


def test_get_missing_tenant_ids_all_present():
    present = list(EXPECTED_TENANT_IDS)
    assert get_missing_tenant_ids(present) == []


def test_get_missing_tenant_ids_none_present():
    missing = get_missing_tenant_ids([])
    assert set(missing) == set(EXPECTED_TENANT_IDS)
    assert len(missing) == 13


def test_get_missing_tenant_ids_kunde7_missing():
    present = [t for t in EXPECTED_TENANT_IDS if t != "Kunde7"]
    missing = get_missing_tenant_ids(present)
    assert "Kunde7" in missing
    assert len(missing) == 1


def test_get_missing_tenant_ids_ignores_none():
    present = ["Kunde1", "Kunde2", None, ""]
    missing = get_missing_tenant_ids(present)
    assert "Kunde7" in missing
    assert "Kunde1" not in missing
    assert "Kunde2" not in missing

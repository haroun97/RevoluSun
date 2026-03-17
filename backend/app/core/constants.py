"""
Domain constants and helpers for tenant and meter metadata.

Expected tenants are read from document/tenant_config.json so we can detect
"missing tenants" (e.g. Kunde7) when they have no data in the Excel file.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


def _tenant_config_path() -> Path:
    """
    Path to the tenant config file (document/tenant_config.json).

    That file should be JSON with: { "expected_tenants": ["Kunde1", "Kunde2", ...] }.
    We go up from this file: core -> app -> backend, then into document/.
    """
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root.parent / "document" / "tenant_config.json"


@lru_cache(maxsize=1)
def expected_tenant_ids() -> list[str]:
    """
    List of tenant IDs we expect for this dataset (from tenant_config.json).

    Used to report which tenants are missing from the data. If the file is
    missing or invalid, we return an empty list (no missing-tenant detection).
    """
    path = _tenant_config_path()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []
    tenants = data.get("expected_tenants", [])
    return [t for t in tenants if isinstance(t, str) and t.strip()]


# Alias used by tests and other code
EXPECTED_TENANT_IDS = expected_tenant_ids()


def get_missing_tenant_ids(present_tenant_ids: list[str]) -> list[str]:
    """
    Which expected tenants have no data in the dataset.

    Compares the config list (expected) with the list of tenants that
    actually appear in the data; returns the difference, sorted.
    """
    expected = set(expected_tenant_ids())
    if not expected:
        return []
    present_set = {t for t in present_tenant_ids if t}
    return sorted(expected - present_set)


def tenant_id_sort_key(tenant_id: str | None) -> tuple[int, int]:
    """
    Sort key so tenants appear as Kunde1, Kunde2, ... Kunde9, Kunde10 (natural order).

    Returns (0, n) for KundeN; (1, 0) for others so Kunde* come first.
    """
    if not tenant_id or not isinstance(tenant_id, str):
        return (1, 0)
    s = tenant_id.strip()
    if s.startswith("Kunde"):
        try:
            n = int(s[5:])
            return (0, n)
        except ValueError:
            pass
    return (1, 0)


def canonical_tenant_id(tenant_id: str | None) -> str:
    """
    Normalize tenant ID so Kunde01 and Kunde1 both become Kunde1.

    Used when we need a single consistent name per tenant (e.g. to avoid duplicates).
    """
    if not tenant_id or not isinstance(tenant_id, str):
        return tenant_id or ""
    s = tenant_id.strip()
    if s.startswith("Kunde"):
        try:
            n = int(s[5:])
            return f"Kunde{n}"
        except ValueError:
            pass
    return s


def coverage_entry_sort_key(entry: dict) -> tuple[int, int, str]:
    """
    Sort key for the coverage table: building_total first, then pv, then tenants.

    Returns (type_order, kunde_num, meter_id). type_order: 0=building, 1=pv, 2=tenant.
    Tenants are ordered Kunde1, Kunde2, ... Kunde13.
    """
    meter_id = (entry.get("meter_id") or "").strip()
    meter_type = (entry.get("meter_type") or "").strip()
    if meter_id == "building_total" or meter_type == "building_total":
        return (0, 0, meter_id)
    if meter_id == "pv" or meter_type == "pv":
        return (1, 0, meter_id)
    # tenant (KundeN)
    if meter_id.startswith("Kunde"):
        try:
            n = int(meter_id[5:])
            return (2, n, meter_id)
        except ValueError:
            pass
    return (2, 999, meter_id)
